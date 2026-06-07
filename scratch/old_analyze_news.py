def analyze_news(title, description, link, fuente_nombre="Noticias San Juan", rule=None, pub_date_str=None):
    title = clean_html(title)
    description = clean_html(description)

    # ─── GUARDIA ANTI-DUPLICADO: Hash de contenido ────────────────────────────
    # Genera un hash MD5 del título normalizado + fecha de publicación.
    # Si ya procesamos una noticia con este contenido (aunque tenga distinta URL),
    # la descartamos ANTES de hacer cualquier deep fetch o llamada de geocoding.
    content_hash = make_content_hash(title, pub_date_str)
    if is_content_processed(content_hash):
        print(f"[HASH-DUP] Noticia ya procesada (mismo título/fecha, distinta URL): '{title[:80]}...'")
        return None

    text_to_search = (title + " " + description).lower()
    # Evitar falsos positivos de "fuego" y usos figurativos de "impacto" / "giro"
    text_to_search = text_to_search.replace("matafuegos", "").replace("matafuego", "")
    
    # Exclusión de modismos y falsos positivos de "impacto" (que disparan contexto de accidente)
    for term in [
        "fuerte impacto", "gran impacto", "alto impacto", "bajo impacto", 
        "impacto economico", "impacto social", "impacto politico", "impacto ambiental",
        "impacto de la noticia", "causo impacto", "genero impacto", "provoco impacto",
        "dieron un giro", "giro inesperado", "giro en la investigacion", "giro en la causa"
    ]:
        text_to_search = text_to_search.replace(term, "")
        
    if any(black_word in text_to_search for black_word in BLACKLIST_KEYWORDS):
        return None
    if rule and rule.get("ignore_terms"):
        if any(term in text_to_search for term in rule["ignore_terms"]):
            return None


    # ─── FASE 1: Pre-filtro por título/descripción ────────────────────────────
    # Si el título/descripción no contiene ninguna señal relevante (accidente,
    # incendio, viento), se descarta SIN hacer deep fetch para no desperdiciar
    # ancho de banda ni provocar 429 de Nominatim con texto de menús/secciones.
    ALL_CONTEXT_KEYWORDS = CONTEXT_WIND + CONTEXT_FIRE + CONTEXT_ACCIDENT
    if not any(has_keyword_match(text_to_search, kw) for kw in ALL_CONTEXT_KEYWORDS):
        return None

    # ─── FASE 2: Filtros de ubicación ─────────────────────────────────────────
    mentions_other_province = any(prov in text_to_search for prov in BLACKLIST_PROVINCIAS)
    mentions_local = (
        any(loc.lower() in text_to_search for loc in LOCALIDADES) or
        any(dept.lower() in text_to_search for dept in DEPARTAMENTOS)
    )
    title_desc_combined = (title + " " + description).lower()
    if any(re.search(pat, title_desc_combined, re.IGNORECASE) for pat in BLACKLIST_EVENT_LOCATION_PATTERNS):
        return None
    if mentions_other_province and not mentions_local:
        return None

    # ─── FASE 3: Deep fetch (solo si el título tenía señal relevante) ──────────
    # Leer el cuerpo completo para obtener más contexto geográfico y de categoría.
    deep_fetch_enabled = rule.get("deep_fetch", True) if rule else True
    body_text = ""
    if deep_fetch_enabled and link and link.startswith("http"):
        body_text = fetch_article_text(link)
        if body_text:
            text_to_search += " " + body_text.lower()

    # ─── FASE 4: Geocodificación con texto completo ────────────────────────────
    res = geocoding_funnel(title, rule)
    if res and not res[2]:
        lat, lon, is_approx, source, loc_type = res
    else:
        full_res = geocoding_funnel(title + " " + description, rule)
        if full_res:
            lat, lon, is_approx, source, loc_type = full_res
        else:
            lat, lon, is_approx, source, loc_type = None, None, True, 'fallback', 'APPROXIMATE'

    # Intentar mejorar coordenadas con el cuerpo si aún son aproximadas
    if body_text and (is_approx or lat is None):
        deep_res = geocoding_funnel(body_text, rule)
        if deep_res:
            d_lat, d_lon, d_is_approx, d_source, d_loc_type = deep_res
            if not d_is_approx or lat is None:
                lat, lon, is_approx, source, loc_type = d_lat, d_lon, d_is_approx, d_source, d_loc_type

    # ─── FASE 5: Detección de categoría ────────────────────────────────────────
    # Usamos title_desc_combined para verificar el CONTEXTO principal (evita falsos
    # positivos si el cuerpo menciona "impactó" en una nota de un puma, por ej).
    # Usamos text_to_search (que incluye el cuerpo) para buscar detalles en el MAPPING.
    detected_category = None
    
    if any(has_keyword_match(title_desc_combined, word) for word in CONTEXT_WIND):
        for slug, keywords in WIND_MAPPING.items():
            if any(has_keyword_match(text_to_search, kw) for kw in keywords):
                detected_category = slug
                break
                
    if not detected_category and any(has_keyword_match(title_desc_combined, word) for word in CONTEXT_FIRE):
        is_firearm = any(x in text_to_search for x in [
            "arma de fuego", "armas de fuego", "disparó", "disparo", "dispararon",
            "balearon", "balear", "herido de bala", "herida de bala", "impactos de bala", 
            "recibio disparos", "recibió disparos", "tiros", "disparos", "balacera", "balazo"
        ])
        is_animal = "llamas" in text_to_search and any(a in text_to_search for a in ["animal", "aves", "guanaco", "fauna", "especie", "ejemplar"])
        if not (is_firearm or is_animal):
            detected_category = "incendio"
            for slug, fire_kws in FIRE_MAPPING.items():
                if any(has_keyword_match(text_to_search, kw) for kw in fire_kws):
                    detected_category = slug
                    break
                    
    if not detected_category and any(has_keyword_match(title_desc_combined, word) for word in CONTEXT_ACCIDENT):
        # Guardia contra falsos positivos: incidentes de violencia armada, disparos o asaltos
        # que no son siniestros viales sino delitos policiales o crímenes de sangre.
        is_armed_violence = any(x in text_to_search for x in [
            "balearon", "balear", "herido de bala", "herida de bala", "impactos de bala", 
            "recibio disparos", "recibió disparos", "tiros", "disparos", "apuñalaron", 
            "apunalar", "apuñaló", "apunalo", "herido de arma blanca", "puñalada", "punialada"
        ])
        has_real_crash = any(x in text_to_search for x in ["chocó contra", "choco contra", "colisionaron", "embistió a", "embistio a"])
        
        if is_armed_violence and not has_real_crash:
            # Es un hecho policial de sangre, no un accidente vial. Se saltea.
            pass
        else:
            vuelco_context = [
                "auto", "automóvil", "automovil", "vehículo", "vehiculo", "coche",
                "camión", "camion", "camioneta", "colectivo", "micro", "ómnibus", "omnibus", "bus",
                "moto", "motocicleta", "motociclista", "ciclomotor", "rodado",
                "ciclista", "bicicleta", "bici", "peatón", "peatona", "transeúnte", "transeunte",
                "utilitario", "furgón", "furgon", "trafic", "ambulancia", "patrullero",
                "ruta", "calle", "avenida", "av.", "autopista", "carretera", "asfalto", "calzada",
                "banquina", "zanja", "cuneta", "bache", "semáforo", "semaforo", "esquina",
                "conductor", "conductores", "pasajero", "pasajeros", "volcadura", "tránsito", "transito", "vial"
            ]
            false_positives = [
                "vuelco inesperado", "vuelco en la causa", "vuelco en la investigacion",
                "vuelco en la investigación", "vuelco en el caso", "giro inesperado",
                "cayó detenido", "cayo detenido", "cayó preso", "cayo preso",
                "cayó la banda", "cayo la banda", "cayó una banda", "cayo una banda",
                "cayó por el robo", "cayo por el robo", "cayó por robo", "cayo por robo",
                "cayó por robar", "cayo por robar", "cayó in fraganti", "cayo in fraganti",
                "cayó con las manos", "cayo con las manos", "cayó tras", "cayo tras",
                "cayó acusado", "cayo acusado", "caída de granizo", "caida de granizo",
                "caída del cabello", "caida del cabello", "caída de las ventas", "caida de las ventas",
                "caída del consumo", "caida del consumo"
            ]
        for slug, keywords in ACCIDENT_MAPPING.items():
            if any(has_keyword_match(text_to_search, kw) for kw in keywords):
                if slug == "vuelco":
                    if any(fp in text_to_search for fp in false_positives):
                        continue
                    if not any(ctx in text_to_search for ctx in vuelco_context):
                        continue
                detected_category = slug
                break

    if not detected_category or lat is None:
        return None

    is_fatal = any(has_keyword_match(text_to_search, kw) for kw in FATAL_KEYWORDS)
    
    from email.utils import parsedate_to_datetime
    
    pub_date = datetime.now()
    if pub_date_str:
        try:
            # RSS pubDate typically uses RFC 2822
            pub_date = parsedate_to_datetime(pub_date_str)
            # Remove timezone info to match our DB format (naive local)
            pub_date = pub_date.replace(tzinfo=None)
        except Exception as e:
            print(f"[WARNING] No se pudo parsear pubDate '{pub_date_str}': {e}")
            pass
            
    event_date = pub_date
    if "ayer" in text_to_search or "anoche" in text_to_search:
        from datetime import timedelta
        event_date = pub_date - timedelta(days=1)
        
    # Persistir el hash ANTES de retornar para que futuras corridas no re-geocodifiquen esta noticia
    save_content_hash(content_hash, link or '')

    # Concatenar la descripción corta y el cuerpo completo para que la API de Laravel 
    # tenga todo el texto disponible para la extracción de nombres de víctimas y análisis.
    full_description = description if description else ""
    if body_text:
        # Evitar duplicar el copete si ya está al inicio del cuerpo
        cleaned_body = body_text.strip()
        if full_description and cleaned_body.startswith(full_description[:100]):
            full_description = cleaned_body
        else:
            full_description = (full_description + "\n\n" + cleaned_body).strip()
            
    if not full_description:
        full_description = "Sin descripción."

    return {
        "etiqueta": detected_category,
        "titulo": title[:250],
        "descripcion": full_description,
        "latitud": lat,
        "longitud": lon,
        "is_approximate": is_approx,
        "source": source,
        "location_type": loc_type,
        "is_fatal": is_fatal,
        "fuente_nombre": fuente_nombre,
        "fuente_url": link,
        "event_date": event_date.strftime("%Y-%m-%d %H:%M:%S"),
        "source_publish_date": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
        "verificado": False
    }

