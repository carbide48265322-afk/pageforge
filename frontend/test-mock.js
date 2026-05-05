/**
 * Mock系统快速测试脚本
 * 在浏览器控制台中运行此脚本测试mock功能
 */

(function() {
  console.log('🧪 Mock系统快速测试开始...');

  // 测试1: 检查mock服务是否加载
  console.log('\n1. 检查mock服务加载状态:');
  if (window.simpleMock) {
    console.log('✅ 简化版mock服务已加载');
    console.log('   状态:', window.simpleMock.status);
  } else {
    console.log('❌ 简化版mock服务未加载');
  }

  if (window.mockService) {
    console.log('✅ 完整版mock服务已加载');
    console.log('   状态:', window.mockService.status);
  } else {
    console.log('❌ 完整版mock服务未加载');
  }

  // 测试2: 检查环境变量
  console.log('\n2. 检查环境变量:');
  console.log('   VITE_MOCK_MODE:', import.meta.env.VITE_MOCK_MODE);
  console.log('   开发环境:', import.meta.env.DEV);

  // 测试3: 检查URL参数
  console.log('\n3. 检查URL参数:');
  const urlParams = new URLSearchParams(window.location.search);
  console.log('   mock参数:', urlParams.get('mock'));

  // 测试4: 手动启用mock
  console.log('\n4. 手动测试mock:');
  if (window.simpleMock) {
    console.log('   启用mock模式...');
    window.simpleMock.enable();
    console.log('   当前状态:', window.simpleMock.status);
  }

  // 测试5: API拦截测试
  console.log('\n5. API拦截测试:');
  fetch('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => {
    console.log('   API响应状态:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('   API响应数据:', data);
    console.log('✅ Mock拦截测试成功');
  })
  .catch(error => {
    console.log('❌ Mock拦截测试失败:', error.message);
  });

  console.log('\n🧪 Mock系统快速测试完成');
  console.log('\n💡 使用提示:');
  console.log('   - 在URL中添加 ?mock=true 启用mock模式');
  console.log('   - 在控制台输入 simpleMock.toggle() 切换mock模式');
  console.log('   - 访问 /mock-test.html 查看详细测试页面');
})();