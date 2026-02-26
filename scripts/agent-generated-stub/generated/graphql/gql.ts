/**
 * Stub for building without GraphQL codegen (no cloud API / no schema).
 * Passes through the query string so the extension builds; runtime calls
 * to the cloud API will still work if the backend is available.
 */
import type { TypedDocumentString } from './graphql'

export function graphql<TResult, TVariables>(
  strings: TemplateStringsArray,
  ...values: unknown[]
): TypedDocumentString<TResult, TVariables> {
  const parts = [strings[0]]
  for (let i = 0; i < values.length; i++) {
    parts.push(String(values[i]), strings[i + 1])
  }
  return parts.join('') as TypedDocumentString<TResult, TVariables>
}
