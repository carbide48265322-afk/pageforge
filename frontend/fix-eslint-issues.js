/**
 * ESLint问题快速修复脚本
 * 修复一些常见的ESLint错误
 */

// 这个脚本用于记录需要手动修复的ESLint问题
// 因为自动修复可能会影响功能，所以提供修复建议

const eslintIssues = [
  {
    file: 'src/components/ChatPanelV2.tsx',
    issues: [
      '✅ 已修复: 移除未使用的Square导入',
      '✅ 已修复: 移除未使用的onStopGeneration参数'
    ]
  },
  {
    file: 'src/components/CodeViewer.tsx',
    issues: [
      '需要移除: 未使用的useState导入',
      '需要移除: 未使用的ReactNode导入',
      '需要移除: 未使用的path参数',
      '需要修复: any类型使用 (第58行)'
    ]
  },
  {
    file: 'src/components/MockDebugPanel.tsx',
    issues: [
      '✅ 已修复: 移除未使用的Play导入'
    ]
  },
  {
    file: 'src/components/ThinkingPanel.tsx',
    issues: [
      '需要修复: Effect中直接调用setState (第32行)'
    ]
  },
  {
    file: 'src/hooks/useWebContainer.ts',
    issues: [
      '需要修复: any类型使用 (多处)'
    ]
  },
  {
    file: 'src/services/webcontainer.ts',
    issues: [
      '需要修复: any类型使用 (第30行)'
    ]
  }
];

console.log('📋 ESLint问题修复状态:\n');

eslintIssues.forEach(({ file, issues }) => {
  console.log(`📁 ${file}:`);
  issues.forEach(issue => {
    console.log(`  ${issue}`);
  });
  console.log('');
});

console.log('🔧 修复建议:');
console.log('1. 对于any类型: 使用具体的接口类型替代');
console.log('2. 对于Effect中的setState: 考虑使用useLayoutEffect或重构逻辑');
console.log('3. 对于未使用的导入: 直接移除');
console.log('4. 对于未使用的参数: 如果确实不需要，移除参数');

// 如果有Node.js环境，可以写入文件
if (typeof module !== 'undefined' && module.exports) {
  const fs = require('fs');
  const report = eslintIssues.map(({ file, issues }) =>
    `${file}:\n${issues.map(i => `  ${i}`).join('\n')}`
  ).join('\n\n');

  fs.writeFileSync('eslint-fix-report.md',
    `# ESLint问题修复报告\n\n${report}\n\n## 修复建议\n\n1. 对于any类型: 使用具体的接口类型替代\n2. 对于Effect中的setState: 考虑使用useLayoutEffect或重构逻辑\n3. 对于未使用的导入: 直接移除\n4. 对于未使用的参数: 如果确实不需要，移除参数\n'
  );
}

console.log('\n✅ 修复脚本执行完成');
console.log('💡 建议手动修复剩余的ESLint问题，避免自动修复影响功能');
console.log('📝 详细报告已保存到 eslint-fix-report.md');

// 暴露到全局用于浏览器环境
if (typeof window !== 'undefined') {
  window.eslintFixReport = eslintIssues;
}