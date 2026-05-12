<?php

namespace App\Console\Commands;

use Illuminate\Console\Attributes\Description;
use Illuminate\Console\Attributes\Signature;
use Illuminate\Console\Command;

#[Signature('incidents:scrape')]
#[Description('Ejecuta el scraper de Python para obtener nuevos incidentes vía RSS')]
class ScrapeIncidents extends Command
{
    /**
     * Execute the console command.
     */
    public function handle()
    {
        $this->info('Iniciando el scraper de incidentes...');

        $scriptPath = base_path('scrapers/rss_scraper.py');
        
        // Ejecutar el script de python
        // Usamos shell_exec para simplificar en Windows/Linux si Process no está disponible
        $output = shell_exec("python \"$scriptPath\" 2>&1");

        if (is_null($output)) {
            $this->error('No se pudo ejecutar el script de Python. Verifica que python esté en el PATH.');
            return 1;
        }

        $this->info('Salida del scraper:');
        $this->line($output);
        
        return 0;
    }
}
