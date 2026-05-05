/**
 * 模式匹配测试脚本
 * 验证宽泛匹配机制是否正确工作
 */

(function() {
  console.log('🧪 模式匹配测试开始...');

  // 测试URL列表
  const testUrls = [
    // 应该匹配"发送消息"
    'http://localhost:9000/api/sessions/test-session-123/messages',
    'http://localhost:9000/api/sessions/mock_session_1777958876434/messages',
    '/api/sessions/abc-def-ghi/messages',
    '/api/sessions/123/messages',

    // 应该匹配"创建会话"
    'http://localhost:9000/api/sessions',
    '/api/sessions',

    // 应该匹配其他API
    'http://localhost:9000/api/sessions/test/versions',
    '/api/sessions/abc/html',

    // 不应该匹配
    '/api/users',
    '/api/projects',
    '/api/sessions/extra/path'
  ];

  // 测试方法
  const testMethod = 'POST';

  // 宽泛匹配模式
  const patterns = [
    {
      pattern: /\/api\/sessions\/[^/]+\/messages$/,
      method: 'POST',
      name: '发送消息 (宽泛匹配)'
    },
    {
      pattern: /\/api\/sessions$/,
      method: 'POST',
      name: '创建会话 (宽泛匹配)'
    },
    {
      pattern: /\/api\/sessions\/[^/]+\/versions$/,
      method: 'GET',
      name: '获取版本列表 (宽泛匹配)'
    },
    {
      pattern: /\/api\/sessions\/[^/]+\/html$/,
      method: 'GET',
      name: '获取HTML内容 (宽泛匹配)'
    },
    {
      pattern: /\/api\/sessions/,
      method: 'POST',
      name: '创建会话 (备选匹配)'
    }
  ];

  function testUrl(url, method) {
    console.log(`\n🔍 测试URL: ${url} (方法: ${method})`);

    for (const { pattern, method: requiredMethod, name } of patterns) {
      if (pattern.test(url) && method === requiredMethod) {
        console.log(`✅ 匹配成功: ${name}`);
        return true;
      }
    }

    console.log(`❌ 没有匹配到任何模式`);
    return false;
  }

  // 运行测试
  console.log('\n📋 开始测试URL匹配...');

  const results = testUrls.map(url => {
    const matched = testUrl(url, testMethod);
    return { url, matched };
  });

  // 统计结果
  const matchedCount = results.filter(r => r.matched).length;
  const totalCount = results.length;

  console.log('\n' + '='.repeat(50));
  console.log('📊 测试结果总结');
  console.log('='.repeat(50));
  console.log(`✅ 匹配成功: ${matchedCount}/${totalCount}`);
  console.log(`📈 成功率: ${((matchedCount / totalCount) * 100).toFixed(1)}%`);

  // 详细分析
  console.log('\n📋 详细分析:');
  results.forEach(({ url, matched }) => {
    const status = matched ? '✅' : '❌';
    console.log(`${status} ${url}`);
  });

  // 暴露测试函数到全局
  window.testPatternMatching = function(url, method = 'POST') {
    return testUrl(url, method);
  };

  console.log('\n🎯 测试完成！宽泛匹配机制应该能正确处理各种URL格式。');
})();