const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('Setting up stream-clipper...');

// Check Python
 try {
  execSync('python --version', { stdio: 'ignore' });
  console.log('✓ Python detected');
} catch {
  console.error('✗ Python not found. Please install Python 3.8+');
  process.exit(1);
}

// Install Python dependencies
const requirementsPath = path.join(__dirname, '..', 'requirements.txt');
if (fs.existsSync(requirementsPath)) {
  console.log('Installing Python dependencies...');
  try {
    execSync(`pip install -r "${requirementsPath}"`, { stdio: 'inherit' });
    console.log('✓ Python dependencies installed');
  } catch (error) {
    console.error('✗ Failed to install Python dependencies');
    console.error('Please run manually: pip install -r requirements.txt');
  }
}

console.log('\nSetup complete! You can now use:');
console.log('  stream-clipper download <url>');
console.log('  stream-clipper --help');
