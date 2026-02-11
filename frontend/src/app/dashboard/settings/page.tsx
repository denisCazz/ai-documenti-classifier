import SettingsForm from "@/components/settings-form";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Configurazione Organizzazione
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Configura la API key, il modello AI e il system prompt per la tua
          organizzazione. Solo gli admin possono modificare queste impostazioni.
        </p>
      </div>

      <SettingsForm />
    </div>
  );
}
