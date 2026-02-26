import path from 'node:path'
import { includeIgnoreFile } from '@eslint/compat'
import type { CodegenConfig } from '@graphql-codegen/cli'

// biome-ignore lint/style/noProcessEnv: env needed for codegen config
const env = process.env

// Schema: URL (introspection) or local file path. No need for BrowserOS-workers repo.
const schemaUrl = env.GRAPHQL_SCHEMA_URL
const schemaPath = env.GRAPHQL_SCHEMA_PATH
const schema = schemaUrl || schemaPath
if (!schema) {
  throw new Error(
    'Set GRAPHQL_SCHEMA_URL or GRAPHQL_SCHEMA_PATH in .env.development.\n' +
      '  GRAPHQL_SCHEMA_URL: GraphQL endpoint for introspection (e.g. https://api.browseros.com/graphql).\n' +
      '  GRAPHQL_SCHEMA_PATH: local path to schema.graphql (e.g. from BrowserOS-workers repo).',
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
