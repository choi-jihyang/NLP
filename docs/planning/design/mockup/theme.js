/* 라이트 · 다크 전환. 상단 바(.nav-right)에 버튼을 붙이고, 고른 값은 이 브라우저에 기억한다 */
(function () {
  var KEY = 'tg-theme'
  var saved = null
  try { saved = localStorage.getItem(KEY) } catch (e) {}
  var dark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
  var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>'
  document.addEventListener('DOMContentLoaded', function () {
    var host = document.querySelector('.nav-right')
    if (!host) return
    var btn = document.createElement('button')
    btn.className = 'theme-btn'
    var paint = function () {
      var isDark = document.documentElement.getAttribute('data-theme') === 'dark'
      btn.innerHTML = isDark ? SUN : MOON
      btn.setAttribute('aria-label', isDark ? '밝은 화면으로' : '어두운 화면으로')
      btn.title = btn.getAttribute('aria-label')
    }
    btn.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'
      document.documentElement.setAttribute('data-theme', next)
      try { localStorage.setItem(KEY, next) } catch (e) {}
      paint()
    })
    paint()
    host.appendChild(btn)
  })
})()

/* 짧은 알림: tgToast('저장했어요') */
window.tgToast=function(t){var el=document.querySelector('.toast');if(!el){el=document.createElement('div');el.className='toast';document.body.appendChild(el)}
  el.textContent=t;el.classList.add('on');clearTimeout(window.tgToast._t);window.tgToast._t=setTimeout(function(){el.classList.remove('on')},1800)}
