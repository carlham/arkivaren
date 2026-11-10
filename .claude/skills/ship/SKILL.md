---
name: ship
description: Wrap up a finished milestone, update the docs and merge the branch into main after the user's go.
argument-hint: [spec file, optional]
disable-model-invocation: true
---

# Ship

## Check first

Stop and tell the user if any of these are not true.

- Every "ferdig når" point is ✅, or the user has said explicitly that a point can wait.
- The last review has no open "må fikses" findings.
- The test suite passes.

## Wrap up

1. Copy the entries under Beslutninger in the spec into docs/decisions.md, using the format and order already in that file.
2. Mark the milestone ✅ in docs/plan.md.
3. Set the spec status to `ferdig`.
4. Write a reading guide for the milestone in Norwegian, to use as the pull request description. Do not put it in the repo or commit it: save it as a file in the scratchpad directory, and keep the text so you can show it to the user. List the files in the order to read them. For each file, one sentence about what it does and its most important functions with `file:line`. Mark the parts the user should read and be able to explain themselves. Keep it to one page.
5. Commit these changes on the milestone branch.
6. Write a short summary with three parts. What changed. What the user should test themselves (as CLAUDE.md asks). What was left out or noticed along the way.

## Gate 1: push and open a pull request

Ask "Push mNN-short-name and open a pull request?" and wait. Only an explicit go counts. This pushes the milestone branch only, never main.

Then run `git push -u origin <branch>`.

Build the pull request link from `git remote get-url origin`: `https://github.com/<owner>/<repo>/compare/main...<branch>?expand=1`. Give it to the user, together with the reading guide from step 4 written out in full, which they can paste as the description. If `gh` is installed, run `gh pr create --base main --head <branch> --title "MNN Name" --body-file <the guide in the scratchpad directory>` instead and give the link it prints.

Tell the user to read the diff in the browser, under "Files changed", or commit by commit, with the reading guide next to it.

## Gate 2: merge

Ask "Merge the pull request for mNN-short-name?" and wait. Only an explicit go counts. The user may also press "Merge pull request" in the browser. With `gh`, run `gh pr merge --merge`.

After the merge, run `git checkout main` and `git pull`. Never push main yourself. If the user wants a local merge instead of the browser, run `git merge --no-ff <branch>` on main and ask separately before `git push origin main`.
