import { existsSync } from 'node:fs'
import path from 'node:path'
import { includeIgnoreFile } from '@eslint/compat'
import type { CodegenConfig } from '@graphql-codegen/cli'

// biome-ignore lint/style/noProcessEnv: env needed for codegen config
const env = process.env

// Schema: URL (introspection), local path, or bundled schema (same as BrowserOS-agent PR #364).
const schemaUrl = env.GRAPHQL_SCHEMA_URL
const schemaPath =
  env.GRAPHQL_SCHEMA_PATH ?? path.resolve(__dirname, 'schema/schema.graphql')
const schema = schemaUrl || schemaPath
if (!schemaUrl && !existsSync(schemaPath)) {
  throw new Error(
    'No schema found. Set GRAPHQL_SCHEMA_URL (introspection) or GRAPHQL_SCHEMA_PATH in .env.development, ' +
      'or ensure apps/agent/schema/schema.graphql exists (e.g. after pulling BrowserOS-agent with PR #364).',
  )
}

const gitignorePath = path.resolve(__dirname, '.gitignore')

const ignorePatterns = includeIgnoreFile(
  gitignorePath,
  'Imported .gitignore patterns',
)

const ignoresList = ignorePatterns.ignores?.map((each) => `!${each}`) ?? []

const config: CodegenConfig = {
  schema,
  documents: ['./**/*.tsx', './**/*.ts', ...ignoresList],
  ignoreNoDocuments: true,
  generates: {
    './generated/graphql/': {
      preset: 'client',
      config: {
        documentMode: 'string',
      },
    },
    './generated/graphql/schema.graphql': {
      plugins: ['schema-ast'],
      config: {
        includeDirectives: true,
      },
    },
  },
}

export default config
