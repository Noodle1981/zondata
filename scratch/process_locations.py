import json

# Cargar los datos extraídos
with open(r'C:\Users\Omar Olivera\.gemini\antigravity\brain\a449383e-bf3c-43aa-ac22-b71653a4959b\.system_generated\steps\433\output.txt', 'r', encoding='utf-8') as f:
    data = json.load(f)

hierarchy = {}

def clean_name(name):
    # Quitar espacios y poner en Capitalize (Tipo Título)
    return name.strip().title()

for item in data:
    dept = clean_name(item['zona_departamento'])
    loc = clean_name(item['localidad'])
    
    # Algunas limpiezas específicas para San Juan
    if dept == "Valle Fertil": dept = "Valle Fértil"
    if dept == "Santa Lucia": dept = "Santa Lucía"
    if dept == "San Martin": dept = "San Martín"
    if dept == "Jachal": dept = "Jáchal"
    
    if dept not in hierarchy:
        hierarchy[dept] = set()
    
    hierarchy[dept].add(loc)

# Generar el código PHP del Seeder
php_code = """<?php

namespace Database\Seeders;

use App\Models\Province;
use App\Models\Department;
use App\Models\Locality;
use Illuminate\Database\Seeder;

class LocationSeeder extends Seeder
{
    public function run(): void
    {
        $sj = Province::firstOrCreate(['name' => 'San Juan']);

        $data = [
"""

for dept, localities in sorted(hierarchy.items()):
    php_code += f"            '{dept}' => [\n"
    for loc in sorted(list(localities)):
        # Escapar comillas simples
        loc_escaped = loc.replace("'", "\\'")
        php_code += f"                '{loc_escaped}',\n"
    php_code += "            ],\n"

php_code += """        ];

        foreach ($data as $deptName => $localities) {
            $dept = Department::updateOrCreate(
                ['province_id' => $sj->id, 'name' => $deptName]
            );

            foreach ($localities as $locName) {
                Locality::updateOrCreate(
                    ['department_id' => $dept->id, 'name' => $locName]
                );
            }
        }
    }
}
"""

with open('d:/Zondata/database/seeders/LocationSeeder.php', 'w', encoding='utf-8') as f:
    f.write(php_code)

print("Seeder generado con éxito con toda la jerarquía de Establecimientos.")
