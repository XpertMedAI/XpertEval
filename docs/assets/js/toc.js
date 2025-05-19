document.addEventListener('DOMContentLoaded', function() {
  // 检查页面是否启用了toc
  var isTocEnabled = false;
  
  // 尝试从页面元数据中获取toc设置
  var metaTags = document.getElementsByTagName('meta');
  for (var i = 0; i < metaTags.length; i++) {
    if (metaTags[i].getAttribute('name') === 'toc' && metaTags[i].getAttribute('content') === 'true') {
      isTocEnabled = true;
      break;
    }
  }
  
  // 如果未找到元数据，则假设所有页面都启用toc
  if (isTocEnabled || metaTags.length === 0) {
    // 获取所有h2和h3标题
    var headings = document.querySelectorAll('.main-content h2, .main-content h3');
    
    // 如果页面有标题，则创建目录
    if (headings.length > 0) {
      // 创建目录容器
      var tocContainer = document.createElement('div');
      tocContainer.className = 'toc';
      
      // 创建标题
      var tocTitle = document.createElement('h4');
      tocTitle.textContent = '页面目录';
      tocContainer.appendChild(tocTitle);
      
      // 创建目录列表
      var tocList = document.createElement('ul');
      
      // 遍历标题并添加到目录
      headings.forEach(function(heading) {
        // 确保标题有id
        if (!heading.id) {
          heading.id = heading.textContent.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
        }
        
        var listItem = document.createElement('li');
        var link = document.createElement('a');
        link.href = '#' + heading.id;
        link.textContent = heading.textContent;
        
        // 为h3添加缩进
        if (heading.tagName === 'H3') {
          listItem.style.marginLeft = '15px';
        }
        
        listItem.appendChild(link);
        tocList.appendChild(listItem);
      });
      
      tocContainer.appendChild(tocList);
      
      // 将目录添加到页面
      var mainContent = document.querySelector('.main-content');
      if (mainContent) {
        document.body.insertBefore(tocContainer, mainContent.nextSibling);
      }
    }
  }
}); 