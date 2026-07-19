/**
 * Thin fetch wrapper shared by every subproject when it starts talking to the
 * FastAPI backend. Centralising the base URL means each page doesn't need to
 * know how the app is deployed.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) {
    throw new Error(`API request to ${path} failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}
