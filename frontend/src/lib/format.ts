export const number = (value: number | null | undefined) =>
  value === null || value === undefined
    ? 'Unavailable'
    : value.toLocaleString('en-US', { maximumFractionDigits: 2 })
export const percent = (value: number | null | undefined) =>
  value === null || value === undefined ? 'Unavailable' : `${(value * 100).toFixed(1)}%`
export const time = (value: string | null | undefined) =>
  value
    ? new Date(value).toLocaleString('en-GB', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'UTC',
      }) + ' UTC'
    : 'Unavailable'
