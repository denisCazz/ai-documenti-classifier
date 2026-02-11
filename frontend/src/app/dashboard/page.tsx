export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        Dashboard
      </h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Chat RAG
          </h3>
          <p className="mt-2 text-gray-700 dark:text-gray-300">
            Interroga i tuoi documenti con l&apos;AI.
          </p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Documenti
          </h3>
          <p className="mt-2 text-gray-700 dark:text-gray-300">
            Carica e gestisci la tua knowledge base.
          </p>
        </div>
        <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Settings
          </h3>
          <p className="mt-2 text-gray-700 dark:text-gray-300">
            Configura API key e system prompt.
          </p>
        </div>
      </div>
    </div>
  );
}
