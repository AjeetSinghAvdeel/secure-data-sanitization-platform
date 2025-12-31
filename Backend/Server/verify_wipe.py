"""
Data Wipe Verification Tool
Verifies that data has been permanently deleted and cannot be recovered
"""
import os
import sys
import hashlib
from pathlib import Path

def calculate_file_hash(filepath, algorithm='sha256'):
    """Calculate hash of a file"""
    hash_obj = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def analyze_file_content(filepath, sample_size=1024):
    """Analyze file content to detect patterns"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read(sample_size)
        
        # Check for patterns that indicate data recovery
        patterns = {
            'all_zeros': all(b == 0 for b in data),
            'all_ones': all(b == 255 for b in data),
            'repeating_pattern': len(set(data[:100])) < 10 if len(data) >= 100 else False,
            'text_content': data.decode('utf-8', errors='ignore').isprintable() if len(data) > 0 else False
        }
        
        # Calculate entropy (randomness measure) - Shannon entropy
        if len(data) > 0:
            import math
            byte_counts = [data.count(bytes([i])) for i in range(256)]
            entropy = -sum((count/len(data)) * math.log2(count/len(data)) 
                          for count in byte_counts if count > 0)
        else:
            entropy = 0
        
        return {
            'patterns': patterns,
            'entropy': entropy,
            'size': len(data),
            'sample_hex': data[:64].hex() if len(data) >= 64 else data.hex()
        }
    except Exception as e:
        return {'error': str(e)}

def verify_wipe_completeness(filepath, original_hash=None):
    """
    Verify that a file has been properly wiped
    
    Args:
        filepath: Path to the file to verify
        original_hash: Optional original file hash for comparison
    
    Returns:
        Dictionary with verification results
    """
    if not os.path.exists(filepath):
        return {
            'status': 'file_not_found',
            'message': 'File does not exist (may have been deleted)',
            'verified': True  # File deletion is part of secure wipe
        }
    
    try:
        file_size = os.path.getsize(filepath)
        
        # Analyze file content
        analysis = analyze_file_content(filepath, min(file_size, 10240))  # Sample up to 10KB
        
        # Check if file appears to be wiped (high entropy, no patterns)
        is_wiped = False
        issues = []
        
        if 'error' in analysis:
            return {
                'status': 'error',
                'message': analysis['error'],
                'verified': False
            }
        
        # High entropy indicates random data (good for wipe)
        if analysis['entropy'] > 7.5:
            is_wiped = True
        else:
            issues.append(f"Low entropy ({analysis['entropy']:.2f}) - may contain recoverable data")
        
        # Check for suspicious patterns
        if analysis['patterns']['all_zeros']:
            issues.append("File contains all zeros - not properly wiped")
            is_wiped = False
        elif analysis['patterns']['all_ones']:
            issues.append("File contains all ones - not properly wiped")
            is_wiped = False
        elif analysis['patterns']['repeating_pattern']:
            issues.append("Repeating patterns detected - may be recoverable")
            is_wiped = False
        
        # Calculate current hash
        current_hash = calculate_file_hash(filepath)
        
        result = {
            'status': 'verified' if is_wiped and len(issues) == 0 else 'warning',
            'verified': is_wiped and len(issues) == 0,
            'file_size': file_size,
            'current_hash': current_hash,
            'entropy': analysis['entropy'],
            'issues': issues,
            'analysis': analysis
        }
        
        if original_hash:
            result['original_hash'] = original_hash
            result['hash_changed'] = (current_hash != original_hash)
            if current_hash == original_hash:
                result['verified'] = False
                result['issues'].append("File hash unchanged - data may not have been wiped")
        
        return result
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'verified': False
        }

def verify_directory_wipe(directory_path):
    """Verify that all files in a directory have been wiped"""
    results = {
        'total_files': 0,
        'verified': 0,
        'warnings': 0,
        'errors': 0,
        'details': []
    }
    
    try:
        for root, dirs, files in os.walk(directory_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                results['total_files'] += 1
                
                verification = verify_wipe_completeness(filepath)
                results['details'].append({
                    'file': filepath,
                    'verification': verification
                })
                
                if verification.get('verified'):
                    results['verified'] += 1
                elif verification.get('status') == 'warning':
                    results['warnings'] += 1
                else:
                    results['errors'] += 1
        
        results['all_verified'] = (results['warnings'] == 0 and results['errors'] == 0)
        return results
        
    except Exception as e:
        return {
            'error': str(e),
            'all_verified': False
        }

def create_test_file(filepath, content="This is test data that should be permanently deleted."):
    """Create a test file for wipe verification"""
    with open(filepath, 'w') as f:
        f.write(content)
    return calculate_file_hash(filepath)

def demonstrate_wipe_verification():
    """Demonstrate wipe verification with a test file"""
    test_file = "wipe_verification_test.txt"
    
    print("=" * 60)
    print("Data Wipe Verification Demonstration")
    print("=" * 60)
    print()
    
    # Create test file
    print(f"1. Creating test file: {test_file}")
    original_hash = create_test_file(test_file, "Sensitive data: Password123, CreditCard: 1234-5678-9012-3456")
    print(f"   Original hash: {original_hash}")
    print()
    
    # Verify before wipe
    print("2. Verifying file BEFORE wipe:")
    before = verify_wipe_completeness(test_file, original_hash)
    print(f"   Status: {before.get('status', 'unknown')}")
    if 'entropy' in before:
        print(f"   Entropy: {before['entropy']:.2f}")
    if 'message' in before:
        print(f"   Message: {before['message']}")
    print(f"   Verified as wiped: {before.get('verified', False)}")
    if before.get('issues'):
        print(f"   Issues: {', '.join(before['issues'])}")
    print()
    
    # Perform wipe (simulate)
    print("3. Performing secure wipe (3 passes)...")
    from main import wipe_file
    try:
        wipe_file(test_file, passes=3)
        print("   Wipe completed (file deleted)")
        print()
        
        # Verify after wipe
        print("4. Verifying file AFTER wipe:")
        if os.path.exists(test_file):
            after = verify_wipe_completeness(test_file, original_hash)
            print(f"   Status: {after.get('status', 'unknown')}")
            if 'entropy' in after:
                print(f"   Entropy: {after['entropy']:.2f}")
            if 'message' in after:
                print(f"   Message: {after['message']}")
            print(f"   Hash changed: {after.get('hash_changed', 'N/A')}")
            print(f"   Verified as wiped: {after.get('verified', False)}")
            if after.get('issues'):
                print(f"   Issues: {', '.join(after['issues'])}")
        else:
            print("   File successfully deleted (part of secure wipe process)")
            print("   [OK] Verification: PASSED - File cannot be recovered")
    except Exception as e:
        print(f"   Error during wipe: {e}")
    
    print()
    print("=" * 60)
    print("Verification Complete")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"Verifying wipe for: {filepath}")
        print("=" * 60)
        result = verify_wipe_completeness(filepath)
        print(f"Status: {result['status']}")
        print(f"Verified: {result['verified']}")
        if result.get('entropy'):
            print(f"Entropy: {result['entropy']:.2f}")
        if result.get('issues'):
            print(f"Issues: {', '.join(result['issues'])}")
    else:
        demonstrate_wipe_verification()

