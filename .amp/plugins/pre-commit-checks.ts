import type { PluginAPI } from '@ampcode/plugin'
import path from 'node:path'

export const description =
	'Runs the style, type, docs, distribution, test, and CodeScene code health checks, plus the zizmor workflow audit when a workflow changed, before every agent `git commit` and blocks the commit when any check fails.'

const repoRoot = path.resolve(import.meta.dir, '..', '..')

// The CI lint, unit-test, acceptance-test, and documentation-test jobs, one Python
// version per job.
const checks = [
	'hatch run style:check',
	'hatch run types:check',
	'hatch run docs:build',
	'hatch run distribution:check',
	'hatch run +py=3.11 unit-tests:run',
	'hatch run +py=3.15 unit-tests:run',
	'hatch run +py=3.15 acceptance-tests:run',
	'hatch run +py=3.15 documentation-tests:run',
]

// CodeScene's delta analysis of all uncommitted changes against HEAD; it fails on new
// code health issues and prints them. Not `--staged`: the checks run before git does,
// so files the same command stages are not staged yet. It runs only when the CLI and
// its token are present.
const codeHealthCheck = 'cs delta --git-hook'

// The zizmor audit from the Workflow Security CI job. It runs only when a file under
// `.github/workflows/` differs from HEAD (staged, unstaged, or untracked), for the
// same reason the code health check does not use `--staged`.
const workflowCheck = 'hatch run workflows:check'

// `git commit`, also with global options such as `git -C dir commit`, but not
// `git commit-tree` or a `commit` argument after a command separator.
const gitCommit = /\bgit\b[^;&|\n]*?\scommit(?![\w-])/

const tail = (text: string, lines: number) => text.trimEnd().split('\n').slice(-lines).join('\n')

export default function (amp: PluginAPI) {
	amp.on('tool.call', async (event, ctx) => {
		const shell = amp.helpers.shellCommandFromToolCall(event)
		if (!shell || !gitCommit.test(shell.command)) {
			return { action: 'allow' }
		}
		// Leave commits in other checkouts alone.
		if (shell.dir && path.relative(repoRoot, path.resolve(repoRoot, shell.dir)).startsWith('..')) {
			return { action: 'allow' }
		}

		// Run in a login shell so hatch from `~/.local/bin` is on PATH. hatch-pip-compile
		// may rewrite lockfile headers without changing pins; restore them when they
		// were clean so the checks cannot sneak changes into the commit.
		const script = `
			cd "$1" || exit 1
			shift
			if command -v cs >/dev/null 2>&1 && [ -n "\${CS_ACCESS_TOKEN:-}" ]; then
				set -- "$@" "${codeHealthCheck}"
				export CS_DISABLE_VERSION_CHECK=1
			fi
			if [ -n "$(git status --porcelain -- .github/workflows)" ]; then
				set -- "$@" "${workflowCheck}"
			fi
			git diff --quiet -- requirements/ && locks_clean=true
			failed=0
			for check in "$@"; do
				if ! output="$($check 2>&1)"; then
					printf 'FAILED: %s\n%s\n\n' "$check" "$output"
					failed=1
				fi
			done
			[ "$locks_clean" = true ] && git checkout --quiet -- requirements/
			exit $failed
		`
		ctx.logger.log(`running pre-commit checks for: ${shell.command}`)
		const result = await ctx.$`bash -lc ${script} pre-commit-checks ${repoRoot} ${checks}`
		if (result.exitCode === 0) {
			return { action: 'allow' }
		}
		return {
			action: 'reject-and-continue',
			message: [
				'Commit blocked by .amp/plugins/pre-commit-checks.ts. Fix these failing checks, then commit again.',
				'',
				tail(`${result.stdout}\n${result.stderr}`, 150),
			].join('\n'),
		}
	})
}
