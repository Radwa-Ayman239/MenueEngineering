/**
 * Safe price formatting helper
 * Coerces value to number, falls back to 0 if invalid, then calls toFixed()
 */
export function formatPrice(value: any, digits: number = 2): string {
  const num = Number(value);
  const safe = Number.isFinite(num) ? num : 0;
  return safe.toFixed(digits);
}
