# How to Use Wipe Verification

## Understanding Verification

**Important**: After a secure wipe, files are **deleted**. You cannot verify a file that no longer exists.

## What Can You Verify?

### 1. **Files BEFORE Wiping** (Recommended)
   - Check if a file contains sensitive data
   - See the entropy (randomness) before wipe
   - Get the original hash for comparison

   **Use Case**: Before wiping a device, verify which files contain sensitive data.

### 2. **Test Files** (For Demonstration)
   - Create a test file
   - Verify it (will show low entropy - readable data)
   - Wipe it
   - File will be deleted (verification passed)

   **Use Case**: Testing and demonstrating the wipe process.

### 3. **Files That Were Overwritten But Not Deleted**
   - If a file was overwritten but not yet deleted
   - Verify it shows high entropy (random data)
   - This confirms the wipe worked

   **Use Case**: During the wipe process, before final deletion.

## Step-by-Step Guide

### Scenario 1: Verify Before Wiping

1. **Select a file** that you want to wipe
2. **Click "Verify"** in the Certificates tab
3. **Check the results**:
   - Low entropy (< 7.5) = File contains readable data
   - High entropy (> 7.5) = File contains random/encrypted data
4. **Note the hash** if you want to compare after wipe
5. **Proceed with wipe** if needed

### Scenario 2: Test Wipe Process

1. **Create a test file**:
   ```python
   # Create test file
   with open("test_file.txt", "w") as f:
       f.write("Sensitive data: Password123")
   ```

2. **Verify BEFORE wipe**:
   - Run verification on `test_file.txt`
   - Should show: Low entropy, readable data

3. **Wipe the file**:
   - Use the wipe function
   - File will be deleted

4. **Verify AFTER wipe**:
   - File won't exist (this is correct!)
   - Verification: PASSED - File cannot be recovered

### Scenario 3: Verify During Wipe Process

If you want to verify a file that's being wiped:

1. **Modify the wipe process** to not delete immediately
2. **Verify the file** after overwriting
3. **Check for high entropy** (> 7.5)
4. **Then delete** the file

## What the Results Mean

### High Entropy (> 7.5)
- ✅ **Good**: File contains random data
- File appears to be wiped or encrypted
- Original data likely cannot be recovered

### Low Entropy (< 7.5)
- ⚠️ **Warning**: File contains structured data
- File has NOT been wiped
- Data may be recoverable
- Consider wiping this file

### File Not Found
- ✅ **Perfect**: File was deleted (part of secure wipe)
- This is the expected result after wiping
- Verification: PASSED

## Common Questions

### Q: I wiped a file, but verification says "file not found" - is this bad?
**A**: No! This is **correct**. Secure wipe deletes files. A deleted file cannot be recovered, which is what you want.

### Q: What file should I verify?
**A**: 
- Files you're **about to wipe** (to check if they contain sensitive data)
- **Test files** (to demonstrate the process)
- Files in a directory you want to check

### Q: Can I verify a whole directory?
**A**: Yes, use the directory verification endpoint:
```python
POST /api/verify-directory
{
    "directory_path": "C:/path/to/directory"
}
```

### Q: How do I know if data is really gone?
**A**: 
1. **File is deleted** = Cannot be recovered (best case)
2. **High entropy** = Contains random data (good)
3. **Hash changed** = Original data overwritten (good)
4. **Low entropy** = Still contains readable data (bad - not wiped)

## Example Workflow

```
1. You have sensitive files on a USB drive
   ↓
2. Before wiping, verify a sample file
   → Result: Low entropy (4.5) - contains readable data
   ↓
3. Perform secure wipe on the USB drive
   → Files are overwritten and deleted
   ↓
4. Try to verify the same file
   → Result: File not found
   → Verification: PASSED ✓
   ↓
5. Data is permanently deleted and cannot be recovered
```

## Tips

1. **Verify BEFORE wiping** to document what was there
2. **Save the hash** of important files before wiping
3. **Use test files** to understand the verification process
4. **Check certificates** - they contain verification data
5. **High entropy** doesn't always mean wiped - could be encrypted

## Summary

- **After wipe**: Files are deleted → Verification shows "file not found" → ✅ PASSED
- **Before wipe**: Files exist → Verification shows entropy → Use to check if sensitive data exists
- **Test files**: Create → Verify (low entropy) → Wipe → Verify (file not found) → ✅ PASSED

The verification tool helps you:
- ✅ Confirm files are permanently deleted (file not found)
- ✅ Check if files contain sensitive data before wiping
- ✅ Verify the wipe process worked correctly

