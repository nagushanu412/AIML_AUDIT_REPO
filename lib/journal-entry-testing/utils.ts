/** Format amount in Indian numbering style (e.g. 50,00,000) */
export function formatIndianAmount(amount: number): string {
  if (amount === 0) return "0";

  const str = Math.round(amount).toString();
  const lastThree = str.slice(-3);
  const rest = str.slice(0, -3);

  if (!rest) return lastThree;

  const grouped = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return `${grouped},${lastThree}`;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatRecordCount(count: number): string {
  return count.toLocaleString("en-IN");
}

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
