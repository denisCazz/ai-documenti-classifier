import ChatInterface from "@/components/chat-interface";

export default function ChatPage() {
  return (
    <div className="h-full">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Chat RAG
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Interroga i tuoi documenti con l&apos;intelligenza artificiale.
        </p>
      </div>

      <ChatInterface />
    </div>
  );
}
