<?php

namespace App\Jobs;

use App\Models\Incident;
use App\Models\AlertSubscriber;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Log;

class SendClimateAlert implements ShouldQueue
{
    use Queueable;

    public Incident $incident;

    /**
     * Create a new job instance.
     */
    public function __construct(Incident $incident)
    {
        $this->incident = $incident;
    }

    /**
     * Execute the job.
     */
    public function handle(): void
    {
        $deptId = $this->incident->department_id;
        $phenomenon = $this->incident->phenomenon_type;

        // Si el incidente no tiene fenómeno o es 'ninguno', no mandamos alertas
        if (!$phenomenon || $phenomenon === 'ninguno') {
            return;
        }

        // Buscar suscriptores activos
        $subscribers = AlertSubscriber::where('is_active', true)
            ->where(function ($query) use ($deptId) {
                $query->whereNull('department_id')
                      ->orWhere('department_id', $deptId);
            })
            ->where(function ($query) use ($phenomenon) {
                $query->whereNull('phenomenon_type')
                      ->orWhere('phenomenon_type', $phenomenon);
            })
            ->get();

        Log::info("Enviando alertas para incidente ID: {$this->incident->id} ({$phenomenon}) a " . $subscribers->count() . " suscriptores.");

        foreach ($subscribers as $sub) {
            $message = "🚨 ALERTA CLIMÁTICA: Se reportó un evento de tipo '{$phenomenon}' en " . ($this->incident->department->name ?? 'San Juan') . ". Detalles: '{$this->incident->title}'.";
            
            Log::channel('single')->info("Notificación enviada a {$sub->email} (Tel: {$sub->phone}): {$message}");
            
            $alertLogPath = storage_path('logs/alerts.log');
            @file_put_contents(
                $alertLogPath,
                "[" . now()->toIso8601String() . "] TO: {$sub->email} | MSJ: {$message}\n",
                FILE_APPEND
            );
        }
    }
}
