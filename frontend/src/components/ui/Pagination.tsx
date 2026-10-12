interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;
  return (
    <div className="flex justify-center items-center gap-2 mt-4">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 disabled:opacity-50"
      >
        &larr;
      </button>
      <span className="text-sm text-gray-600 dark:text-gray-400">
        {currentPage} / {totalPages}
      </span>
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 disabled:opacity-50"
      >
        &rarr;
      </button>
    </div>
  );
}