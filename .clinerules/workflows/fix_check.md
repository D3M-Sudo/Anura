After applying fixes
After you apply every fix, verify it did not break anything and actually solved the problem. For each fix:
1. Check the fix itself

Re-read the modified code and confirm the corrected version is syntactically valid
Confirm the fix addresses the root cause, not just the symptom
Confirm the fix does not introduce the same class of bug elsewhere (e.g. if you moved a connect() call, verify it is not now duplicated or in a new wrong position)

2. Check the surrounding code

Read every caller of the modified function/method and verify they are compatible with the new signature or return value
If you changed an attribute name, search the entire codebase for all references to the old name and update them
If you added a new method, verify it is called correctly everywhere it is needed

3. Check for regressions in related files

Identify all files that import from or depend on the modified file
Read the relevant sections of those files and confirm nothing relies on the old behavior you just changed

4. Verify the full flow end to end

Trace the complete execution path that the bug affected, from user action to final UI update, and confirm every step now works correctly
Explicitly state: "The flow is now: [step 1] → [step 2] → [step 3] → [expected result]"

5. Confirm no new except blocks hide the fix

Check that the corrected code path is not wrapped in a broad exception handler that would silently swallow a new error if your fix introduced one

After all fixes are applied, produce a verification report:
### Fix verification: BUG-N
Status: VERIFIED / NEEDS ATTENTION

Change made: [one line description of what was changed]
Callers checked: [list of files/methods that call the modified code]
Flow verified: [user action] → [step] → [step] → [correct outcome]
Regression risk: none / low / medium — [reason]
If any fix cannot be fully verified by static analysis alone (e.g. it requires runtime behavior), explicitly flag it:
Requires runtime test: [describe exactly what to manually test and what the expected result should be]