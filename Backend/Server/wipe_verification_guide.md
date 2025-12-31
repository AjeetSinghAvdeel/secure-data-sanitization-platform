# Data Wipe Verification Guide

## How to Verify Data is Permanently Deleted

### Understanding Secure Wipe

When data is "permanently deleted" using secure wipe:
1. **Overwriting**: Original data is overwritten with random data (multiple passes)
2. **File Deletion**: The file is removed from the filesystem
3. **Verification**: We can verify that original data cannot be recovered

### Verification Methods

#### 1. **Entropy Analysis**
- **High Entropy (7.5+)**: Indicates random data (properly wiped)
- **Low Entropy (<7.5)**: May contain recoverable patterns

#### 2. **Hash Comparison**
- Calculate hash **before** wipe
- Calculate hash **after** wipe
- If hashes are different, data was overwritten

#### 3. **Pattern Detection**
- Check for all zeros (not wiped)
- Check for all ones (not wiped)
- Check for repeating patterns (may be recoverable)
- Check for readable text (not wiped)

#### 4. **File Deletion**
- File should not exist after wipe
- If file exists, it should have random content

### Using the Verification Tool

#### Command Line Usage

```bash
# Verify a specific file
python verify_wipe.py path/to/file.txt

# Run demonstration
python verify_wipe.py
```

#### API Usage

```python
import requests

# Verify a file
response = requests.post("http://localhost:8000/api/verify-wipe", json={
    "file_path": "path/to/file.txt",
    "original_hash": "optional_hash_before_wipe"
})

result = response.json()
print(f"Verified: {result['verified']}")
print(f"Entropy: {result['entropy']}")
```

### Verification Checklist

After a wipe operation, verify:

- [ ] **File is deleted** (or contains random data)
- [ ] **High entropy** (>7.5) if file still exists
- [ ] **Hash changed** from original (if original hash available)
- [ ] **No patterns detected** (no zeros, ones, or repeating patterns)
- [ ] **Certificate generated** with verification data

### Example Verification Workflow

1. **Before Wipe**:
   ```python
   from verify_wipe import calculate_file_hash
   original_hash = calculate_file_hash("sensitive_file.txt")
   print(f"Original hash: {original_hash}")
   ```

2. **Perform Wipe**:
   ```python
   from main import wipe_file
   wipe_file("sensitive_file.txt", passes=3)
   ```

3. **After Wipe - Verify**:
   ```python
   from verify_wipe import verify_wipe_completeness
   result = verify_wipe_completeness("sensitive_file.txt", original_hash)
   
   if result['verified']:
       print("✓ Data permanently deleted - cannot be recovered")
   else:
       print(f"⚠ Issues: {result['issues']}")
   ```

### What Makes Data "Permanently Deleted"?

1. **Multiple Passes**: Overwriting data multiple times makes recovery extremely difficult
   - 1-pass: Basic overwrite
   - 3-pass: NIST SP 800-88 standard
   - 7-pass: DoD 5220.22-M standard

2. **Random Data**: Using cryptographically secure random data prevents pattern analysis

3. **File System Sync**: `os.fsync()` ensures data is written to disk immediately

4. **File Deletion**: Removing the file entry from the filesystem

### Limitations

**Important Notes**:
- On **SSDs with TRIM**: Data may be automatically erased by the drive
- On **magnetic drives**: Multiple passes are more important
- **Encrypted drives**: May require additional steps
- **RAID arrays**: May need special handling

### Best Practices

1. **Always use multiple passes** (3+ recommended)
2. **Verify after wipe** using the verification tool
3. **Keep certificates** as proof of secure deletion
4. **For critical data**: Consider physical destruction
5. **For SSDs**: Consider secure erase commands

### Testing Verification

Run the demonstration:
```bash
python verify_wipe.py
```

This will:
1. Create a test file with sensitive data
2. Show verification before wipe
3. Perform secure wipe
4. Show verification after wipe
5. Confirm data cannot be recovered

### Integration with Tkinter UI

The Tkinter UI automatically:
- Calculates file hashes before wipe
- Stores verification data in certificates
- Provides wipe completion status

### API Endpoints

- `POST /api/verify-wipe` - Verify a single file
- `POST /api/verify-directory` - Verify all files in a directory

### Security Standards

Our wipe process follows:
- **NIST SP 800-88**: Guidelines for Media Sanitization
- **DoD 5220.22-M**: Department of Defense standard
- **GDPR Article 17**: Right to erasure

### Questions?

If you have questions about verification:
1. Check the certificate for verification data
2. Run the verification tool on specific files
3. Review the entropy and hash values
4. Check for any issues reported by the tool

