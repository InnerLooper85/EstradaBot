Run the mandatory session startup verification and report results.

## Steps

1. Run `git fetch origin` to get the latest remote state
2. Run `git branch --show-current` to confirm the active branch
3. Run `git status` to check for uncommitted changes
4. Run `git log --oneline -1` to show the current local commit
5. Run `git log --oneline -1 origin/master` to show the latest remote master commit
6. Compare local vs remote — if the branch is behind, **warn the developer**

## Report Format

```
SESSION CHECK:
  Branch:          <current branch>
  Local commit:    <short hash + message>
  Remote master:   <short hash + message>
  Status:          UP TO DATE | BEHIND BY X COMMITS | UNCOMMITTED CHANGES
  Ready to work:   YES | NO — <reason>
```

If the branch is behind remote or has merge conflicts, do NOT begin work until the developer decides how to handle it.
