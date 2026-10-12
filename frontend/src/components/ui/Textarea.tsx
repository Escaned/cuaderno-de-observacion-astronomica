import type { TextareaHTMLAttributes } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export function Textarea({ label, className = '', ...props }: TextareaProps) {
  return (
    <div>
      {label && <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">{label}</label>}
      <textarea className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-space-500 focus:border-transparent outline-none ${className}`} {...props} />
    </div>
  );
}