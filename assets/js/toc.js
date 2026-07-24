(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    var content = document.getElementById('page-content');
    var toc = document.getElementById('toc');
    if (!content || !toc) return;

    var headings = Array.prototype.filter.call(
      content.querySelectorAll('h1, h2, h3, h4, h5, h6'),
      function (h) { return !!h.id; }
    );
    if (!headings.length) return;

    var heading = document.createElement('div');
    heading.className = 'toc-heading';
    heading.textContent = 'Outline';
    toc.appendChild(heading);

    var root = document.createElement('ul');
    root.className = 'toc-list';
    toc.appendChild(root);

    var stack = [{ level: 0, list: root }];

    headings.forEach(function (h) {
      var level = parseInt(h.tagName.charAt(1), 10);

      var li = document.createElement('li');
      li.className = 'toc-item';

      var row = document.createElement('div');
      row.className = 'toc-row';

      var toggle = document.createElement('span');
      toggle.className = 'toc-toggle';
      row.appendChild(toggle);

      var link = document.createElement('a');
      link.className = 'toc-link';
      link.href = '#' + h.id;
      link.textContent = h.textContent;
      row.appendChild(link);

      li.appendChild(row);

      while (stack.length > 1 && level < stack[stack.length - 1].level) {
        stack.pop();
      }
      var top = stack[stack.length - 1];

      if (level === top.level) {
        top.list.appendChild(li);
      } else {
        var parentList = top.list;
        var lastLi = parentList.lastElementChild;
        if (!lastLi) {
          parentList.appendChild(li);
          stack.push({ level: level, list: parentList });
          return;
        }
        var childList = lastLi.querySelector(':scope > ul');
        if (!childList) {
          childList = document.createElement('ul');
          childList.className = 'toc-list toc-nested';
          lastLi.appendChild(childList);
          lastLi.classList.add('has-children');
        }
        childList.appendChild(li);
        stack.push({ level: level, list: childList });
      }
    });

    toc.addEventListener('click', function (e) {
      var toggle = e.target.closest('.toc-toggle');
      if (toggle) {
        var item = toggle.closest('.toc-item');
        if (item && item.classList.contains('has-children')) {
          item.classList.toggle('toc-collapsed');
        }
      }
    });
  });
})();
