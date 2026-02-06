#!/usr/bin/env node

const { program } = require('commander');
const { execSync } = require('child_process');
const path = require('path');
const chalk = require('chalk');

const SCRIPTS_DIR = path.join(__dirname, '..', 'scripts');

function runPython(script, args = []) {
  const cmd = `python "${path.join(SCRIPTS_DIR, script)}" ${args.join(' ')}`;
  console.log(chalk.blue(`Running: ${cmd}`));
  try {
    execSync(cmd, { stdio: 'inherit', cwd: process.cwd() });
  } catch (error) {
    console.error(chalk.red('Error executing command'));
    process.exit(1);
  }
}

program
  .name('stream-clipper')
  .description('CLI for stream-clipper - Download and clip Bilibili streams')
  .version('1.0.0');

program
  .command('download <url>')
  .description('Download video, danmaku and subtitles from URL')
  .option('-o, --output <dir>', 'Output directory', './downloads')
  .action((url, options) => {
    runPython('download_stream.py', [`"${url}"`, '--output', `"${options.output}"`]);
  });

program
  .command('analyze <danmaku-file>')
  .description('Analyze danmaku density and find peak moments')
  .action((file) => {
    runPython('analyze_danmaku.py', [`"${file}"`]);
  });

program
  .command('clip')
  .description('Clip video with danmaku overlay')
  .requiredOption('-v, --video <path>', 'Video file path')
  .requiredOption('-r, --recommendations <path>', 'Recommendations JSON file')
  .option('-d, --danmaku <path>', 'Danmaku XML file')
  .option('-o, --output <dir>', 'Output directory', './clips')
  .action((options) => {
    const args = [
      '--video', `"${options.video}"`,
      '--recommendations', `"${options.recommendations}"`,
      '--output', `"${options.output}"`
    ];
    if (options.danmaku) {
      args.push('--danmaku', `"${options.danmaku}"`);
    }
    runPython('clip_and_burn.py', args);
  });

program
  .command('upload <clips-dir>')
  .description('Upload clips to Bilibili')
  .option('-t, --template <name>', 'Streamer template name')
  .option('-c, --cookie <path>', 'Cookie file path', 'cookies.json')
  .option('-b, --batch', 'Batch upload all clips', true)
  .action((dir, options) => {
    const args = [`"${dir}"`];
    if (options.template) args.push('--template', options.template);
    if (options.cookie) args.push('--cookie', `"${options.cookie}"`);
    if (options.batch) args.push('--batch');
    runPython('upload_clip.py', args);
  });

program
  .command('full-workflow <url>')
  .description('Complete workflow: download -> analyze -> clip')
  .option('-o, --output <dir>', 'Working directory', './output')
  .action(async (url, options) => {
    console.log(chalk.green('🎬 Starting full workflow...'));
    
    // This would require implementing the full workflow logic
    console.log(chalk.yellow('This command requires implementing the workflow logic'));
    console.log(chalk.gray('For now, please run commands separately:'));
    console.log(chalk.gray('1. stream-clipper download <url>'));
    console.log(chalk.gray('2. stream-clipper analyze <danmaku.xml>'));
    console.log(chalk.gray('3. stream-clipper clip -v <video> -r <rec.json>'));
  });

program.parse();
