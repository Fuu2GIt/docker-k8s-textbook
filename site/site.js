(function () {
  var OS_KEY = "docker-k8s-textbook-os";
  var DONE_KEY = "docker-k8s-textbook-done";

  function readDone() {
    try {
      var parsed = JSON.parse(localStorage.getItem(DONE_KEY) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function writeDone(ids) {
    try {
      localStorage.setItem(DONE_KEY, JSON.stringify(ids));
    } catch (e) {}
  }

  function applyOs(os) {
    if (os !== "windows" && os !== "linux") os = "linux";
    document.documentElement.dataset.os = os;
    try {
      localStorage.setItem(OS_KEY, os);
    } catch (e) {}
    document.querySelectorAll("[data-os-choice]").forEach(function (btn) {
      btn.setAttribute("aria-pressed", btn.getAttribute("data-os-choice") === os ? "true" : "false");
    });
  }

  document.querySelectorAll("[data-os-choice]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      applyOs(btn.getAttribute("data-os-choice"));
    });
  });

  applyOs(document.documentElement.dataset.os || "linux");

  function paintDone() {
    var done = readDone();
    var set = {};
    done.forEach(function (id) { set[id] = true; });
    document.querySelectorAll("[data-done]").forEach(function (box) {
      box.checked = !!set[box.getAttribute("data-done")];
    });
    document.querySelectorAll("a[data-chapter]").forEach(function (link) {
      link.classList.toggle("is-done", !!set[link.getAttribute("data-chapter")]);
    });
    var count = document.getElementById("progress-count");
    if (count) {
      var total = count.getAttribute("data-total") || "0";
      var n = 0;
      document.querySelectorAll("[data-chapter-row]").forEach(function (row) {
        if (set[row.getAttribute("data-chapter-row")]) n += 1;
      });
      count.textContent = n + " / " + total + " 章";
    }
  }

  document.querySelectorAll("[data-done]").forEach(function (box) {
    box.addEventListener("change", function () {
      var id = box.getAttribute("data-done");
      var done = readDone().filter(function (item) { return item !== id; });
      if (box.checked) done.push(id);
      writeDone(done);
      paintDone();
    });
  });

  paintDone();

  document.querySelectorAll("pre").forEach(function (pre) {
    var code = pre.querySelector("code");
    if (!code) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy";
    btn.textContent = "コピー";
    btn.addEventListener("click", function () {
      var text = code.textContent;
      function ok() {
        btn.textContent = "コピーしました";
        setTimeout(function () { btn.textContent = "コピー"; }, 1600);
      }
      function fail() {
        btn.textContent = "選択してコピーしてください";
        setTimeout(function () { btn.textContent = "コピー"; }, 2000);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(ok, fail);
      } else {
        fail();
      }
    });
    pre.appendChild(btn);
  });

  var input = document.getElementById("search");
  var results = document.getElementById("search-results");
  var root = document.body.getAttribute("data-root") || "";
  if (input && results && window.SEARCH_INDEX) {
    function norm(value) {
      return String(value || "").toLowerCase().replace(/\s+/g, " ").trim();
    }
    function show(query) {
      results.innerHTML = "";
      var q = norm(query);
      if (!q) return;
      var terms = q.split(" ");
      var found = window.SEARCH_INDEX.filter(function (item) {
        var hay = norm(item.title + " " + item.text);
        return terms.every(function (term) { return hay.indexOf(term) !== -1; });
      }).map(function (item) {
        var title = norm(item.title);
        var text = norm(item.text);
        var score = item.href.indexOf("chapters/") === 0 ? 2 : 0;
        terms.forEach(function (term) {
          if (title.indexOf(term) !== -1) score += 5;
          if (text.indexOf(term) !== -1) score += 1;
        });
        return { item: item, score: score };
      }).sort(function (a, b) { return b.score - a.score; }).slice(0, 20).map(function (entry) { return entry.item; });
      found.forEach(function (item) {
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = root + item.href;
        a.textContent = item.title;
        li.appendChild(a);
        results.appendChild(li);
      });
      if (!found.length) {
        var empty = document.createElement("li");
        empty.textContent = "一致する章はありません";
        results.appendChild(empty);
      }
    }
    input.addEventListener("input", function () { show(input.value); });
    var form = input.closest("form");
    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        var first = results.querySelector("a");
        if (first) window.location.href = first.href;
      });
    }
  }
})();
