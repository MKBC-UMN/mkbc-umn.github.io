---
title: "Minnesota Korean Badminton Club"
permalink: /
author_profile: true
classes: wide club-home
---

{% assign hero_images = site.data.hero_images %}
{% assign first_hero = hero_images | first %}

<section class="club-hero">
  <div class="club-hero-copy">
    <p class="club-eyebrow">University of Minnesota - Twin Cities</p>
    <h1>
      <span>Minnesota</span>
      <span><span class="club-k">K</span>orean</span>
      <span>Badminton</span>
      <span>Club</span>
    </h1>
    <p class="club-dek">{{ site.data.club.about }}</p>
    <div class="club-actions">
      <a class="btn btn--primary" href="#join">How to Join</a>
      <a class="btn btn--inverse" href="#policies">Policies</a>
    </div>
  </div>
  <div class="club-hero-media">
    <div class="club-photo-frame">
      <img id="clubHeroImg" src="{{ first_hero.image | relative_url }}" alt="{{ first_hero.alt | default: first_hero.caption }}">
      <p class="club-caption" id="clubHeroCaption">{{ first_hero.caption }}</p>
    </div>
    <div class="club-gallery-meta">
      <div class="club-hero-dots" role="tablist" aria-label="Hero image gallery">
        {% for photo in hero_images %}
          <button class="club-hero-dot{% if forloop.first %} is-active{% endif %}" type="button" data-slide="{{ forloop.index0 }}" aria-label="Show {{ photo.caption }}" aria-selected="{% if forloop.first %}true{% else %}false{% endif %}"></button>
        {% endfor %}
      </div>
    </div>
  </div>
</section>

<section id="schedule" class="club-section schedule-section" aria-labelledby="schedule-title">
  <div class="schedule-heading">
    <div>
      <p class="club-eyebrow">This week's court times</p>
      <h2 id="schedule-title">Cooke Hall 325 — Open Play Badminton</h2>
    </div>
    <div class="schedule-meta">
      <p class="schedule-updated" id="scheduleUpdated">Loading the latest schedule…</p>
      <button class="schedule-copy-button" id="scheduleCopyButton" type="button" disabled>
        <svg aria-hidden="true" viewBox="0 0 24 24" width="14" height="14">
          <path d="M8 7V4c0-1.1.9-2 2-2h8c1.1 0 2 .9 2 2v10c0 1.1-.9 2-2 2h-3v3c0 1.1-.9 2-2 2H5c-1.1 0-2-.9-2-2V9c0-1.1.9-2 2-2h3Zm2 0h3c1.1 0 2 .9 2 2v5h3V4h-8v3Zm3 2H5v10h8V9Z"></path>
        </svg>
        <span>Copy</span>
      </button>
    </div>
  </div>
  <div class="schedule-layout">
    <section class="weekly-summary" aria-labelledby="weeklySummaryTitle">
      <h3 id="weeklySummaryTitle">This Week</h3>
      <div class="schedule-grid" id="badmintonSchedule" aria-live="polite">
        <p class="schedule-status">Loading the latest schedule…</p>
      </div>
    </section>
    <section class="day-timeline" id="dayTimeline" aria-labelledby="timelineDate" hidden>
      <div class="timeline-heading">
        <button class="timeline-arrow" id="timelinePrevious" type="button" aria-label="Previous day">&#8249;</button>
        <h3 id="timelineDate"></h3>
        <button class="timeline-arrow" id="timelineNext" type="button" aria-label="Next day">&#8250;</button>
      </div>
      <div class="timeline-key" aria-hidden="true">
        <span><i class="timeline-key-open"></i>Open play</span>
        <span><i class="timeline-key-reserved"></i>Reserved</span>
      </div>
      <div class="timeline-scroll">
        <div class="timeline-axis" id="timelineAxis" aria-hidden="true"></div>
        <div class="timeline-track" id="timelineTrack"></div>
      </div>
    </section>
  </div>
  <noscript><p class="schedule-status">JavaScript is required to display the live schedule.</p></noscript>
</section>

<script>
(function () {
  var container = document.getElementById("badmintonSchedule");
  var updated = document.getElementById("scheduleUpdated");
  var copyButton = document.getElementById("scheduleCopyButton");
  var timeline = document.getElementById("dayTimeline");
  var timelineDate = document.getElementById("timelineDate");
  var timelineAxis = document.getElementById("timelineAxis");
  var timelineTrack = document.getElementById("timelineTrack");
  var previousButton = document.getElementById("timelinePrevious");
  var nextButton = document.getElementById("timelineNext");
  var endpoint = {{ '/assets/data/badminton_schedule.json' | relative_url | jsonify }};
  var shareMessage = "";
  var scheduleData = null;
  var selectedDay = 0;
  var timelineStart = 5 * 60;
  var timelineEnd = 24 * 60;

  function parseLocalDate(value) {
    var parts = value.split("-").map(Number);
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }

  function formatDate(value) {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      weekday: "short"
    }).format(parseLocalDate(value));
  }

  function formatTime(value) {
    var parts = value.split(":").map(Number);
    var hour = parts[0];
    var suffix = hour >= 12 ? "pm" : "am";
    var displayHour = hour % 12 || 12;
    return displayHour + ":" + String(parts[1]).padStart(2, "0") + " " + suffix;
  }

  function buildShareMessage(data) {
    var lines = [
      "🏸 Cooke Hall 325 Open Play Badminton",
      formatDate(data.week_start) + " – " + formatDate(data.week_end),
      ""
    ];

    data.schedule.forEach(function (day) {
      var times = day.intervals.map(function (interval) {
        return formatTime(interval.start) + "–" + formatTime(interval.end);
      });
      lines.push(formatDate(day.date) + ": " + (times.length ? times.join(" / ") : "No open play scheduled"));
    });

    lines.push("", new URL("#schedule", window.location.href).href);
    return lines.join("\n");
  }

  function minutes(value) {
    var parts = value.split(":").map(Number);
    return parts[0] * 60 + parts[1];
  }

  function timelineLabel(totalMinutes) {
    var hour = totalMinutes / 60;
    if (hour === 24) return "12 AM";
    return (hour % 12 || 12) + " " + (hour >= 12 ? "PM" : "AM");
  }

  function renderTimeline() {
    var day = scheduleData.schedule[selectedDay];
    var reservations = Array.isArray(day.reservations) ? day.reservations : day.intervals.map(function (interval) {
      return { start: interval.start, end: interval.end, type: "open_play" };
    });

    timelineDate.textContent = formatDate(day.date);
    timelineAxis.replaceChildren();
    timelineTrack.replaceChildren();

    for (var tick = timelineStart; tick <= timelineEnd; tick += 60) {
      var label = document.createElement("span");
      label.textContent = timelineLabel(tick);
      label.style.top = ((tick - timelineStart) / (timelineEnd - timelineStart) * 100) + "%";
      timelineAxis.appendChild(label);
    }

    reservations.forEach(function (reservation) {
      var start = Math.max(minutes(reservation.start), timelineStart);
      var end = Math.min(minutes(reservation.end), timelineEnd);
      if (end <= start) return;

      var block = document.createElement("div");
      var isOpenPlay = reservation.type === "open_play";
      block.className = "timeline-block " + (isOpenPlay ? "is-open-play" : "is-reserved");
      block.style.top = ((start - timelineStart) / (timelineEnd - timelineStart) * 100) + "%";
      block.style.height = ((end - start) / (timelineEnd - timelineStart) * 100) + "%";
      block.innerHTML = "<strong>" + (isOpenPlay ? "Open Play Badminton" : "Reserved") + "</strong><span>" +
        formatTime(reservation.start) + " – " + formatTime(reservation.end === "24:00" ? "00:00" : reservation.end) + "</span>";
      timelineTrack.appendChild(block);
    });

    if (reservations.length === 0) {
      var empty = document.createElement("p");
      empty.className = "timeline-empty";
      empty.textContent = "No reservations shown for this day";
      timelineTrack.appendChild(empty);
    }

    previousButton.disabled = selectedDay === 0;
    nextButton.disabled = selectedDay === scheduleData.schedule.length - 1;
    container.querySelectorAll(".schedule-day").forEach(function (card, index) {
      card.classList.toggle("is-selected", index === selectedDay);
      card.setAttribute("aria-pressed", index === selectedDay ? "true" : "false");
    });
  }

  function selectDay(index) {
    selectedDay = Math.max(0, Math.min(index, scheduleData.schedule.length - 1));
    renderTimeline();
  }

  function render(data) {
    if (!data || !Array.isArray(data.schedule) || data.schedule.length !== 7) {
      throw new Error("Unexpected schedule data");
    }

    container.replaceChildren();
    data.schedule.forEach(function (day, index) {
      var article = document.createElement("button");
      article.className = "schedule-day";
      article.type = "button";
      article.setAttribute("aria-label", "Show " + formatDate(day.date) + " timeline");

      var heading = document.createElement("h3");
      heading.textContent = formatDate(day.date);
      article.appendChild(heading);

      if (!Array.isArray(day.intervals) || day.intervals.length === 0) {
        var empty = document.createElement("p");
        empty.className = "schedule-empty";
        empty.textContent = "No open play scheduled";
        article.appendChild(empty);
      } else {
        var list = document.createElement("ul");
        day.intervals.forEach(function (interval) {
          var item = document.createElement("li");
          item.textContent = formatTime(interval.start) + " – " + formatTime(interval.end);
          list.appendChild(item);
        });
        article.appendChild(list);
      }
      article.addEventListener("click", function () {
        selectDay(index);
      });
      container.appendChild(article);
    });

    scheduleData = data;
    var today = new Intl.DateTimeFormat("en-CA", {
      timeZone: data.timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).format(new Date());
    var todayIndex = data.schedule.findIndex(function (day) { return day.date === today; });
    selectedDay = todayIndex >= 0 ? todayIndex : 0;
    timeline.hidden = false;
    renderTimeline();

    var timestamp = new Date(data.scraped_at);
    updated.textContent = "Updated " + new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZone: data.timezone,
      timeZoneName: "short"
    }).format(timestamp);
    shareMessage = buildShareMessage(data);
    copyButton.disabled = false;
  }

  copyButton.addEventListener("click", function () {
    navigator.clipboard.writeText(shareMessage).then(function () {
      copyButton.querySelector("span").textContent = "Copied!";
      window.setTimeout(function () {
        copyButton.querySelector("span").textContent = "Copy";
      }, 1800);
    }).catch(function () {
      copyButton.querySelector("span").textContent = "Try again";
      window.setTimeout(function () {
        copyButton.querySelector("span").textContent = "Copy";
      }, 1800);
    });
  });

  previousButton.addEventListener("click", function () { selectDay(selectedDay - 1); });
  nextButton.addEventListener("click", function () { selectDay(selectedDay + 1); });

  fetch(endpoint, { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) throw new Error("Schedule request failed");
      return response.json();
    })
    .then(render)
    .catch(function () {
      container.innerHTML = '<p class="schedule-status">The current schedule is temporarily unavailable. Please check back soon.</p>';
      updated.textContent = "Schedule unavailable";
    });
})();
</script>

<script>
(function () {
  var photos = [
    {% for photo in hero_images %}
      {
        src: "{{ photo.image | relative_url }}",
        alt: {{ photo.alt | default: photo.caption | jsonify }},
        caption: {{ photo.caption | jsonify }}
      }{% unless forloop.last %},{% endunless %}
    {% endfor %}
  ];

  if (photos.length < 2) return;

  var img = document.getElementById("clubHeroImg");
  var caption = document.getElementById("clubHeroCaption");
  var dots = Array.prototype.slice.call(document.querySelectorAll(".club-hero-dot"));
  var index = 0;
  var timer;

  function showPhoto(nextIndex) {
    index = nextIndex;
    img.classList.add("is-fading");
    window.setTimeout(function () {
      img.src = photos[index].src;
      img.alt = photos[index].alt;
      caption.textContent = photos[index].caption;
      dots.forEach(function (dot, dotIndex) {
        var isActive = dotIndex === index;
        dot.classList.toggle("is-active", isActive);
        dot.setAttribute("aria-selected", isActive ? "true" : "false");
      });
      img.classList.remove("is-fading");
    }, 180);
  }

  function startTimer() {
    timer = window.setInterval(function () {
      showPhoto((index + 1) % photos.length);
    }, 5200);
  }

  dots.forEach(function (dot) {
    dot.addEventListener("click", function () {
      window.clearInterval(timer);
      showPhoto(Number(dot.getAttribute("data-slide")));
      startTimer();
    });
  });

  startTimer();
})();
</script>

<section id="officers" class="club-section">
  <h2>Officers</h2>
  <div class="club-grid officers-grid">
    {% for officer in site.data.officers %}
      <article class="club-card officer-card">
        <div class="officer-photo">
          {% if officer.image and officer.image != "" %}
            {% if officer.image contains "://" %}
              <img src="{{ officer.image }}" alt="{{ officer.name }}">
            {% else %}
              <img src="{{ officer.image | relative_url }}" alt="{{ officer.name }}">
            {% endif %}
          {% else %}
            <img src="{{ '/assets/images/officers/default-officer.svg' | relative_url }}" alt="">
          {% endif %}
        </div>
        <div>
          <h3>{{ officer.name }}{% if officer.field_icon %} <span class="officer-field-icon" title="{{ officer.field }}">{{ officer.field_icon }}</span>{% endif %}</h3>
          <p class="club-card-meta">{{ officer.role }}</p>
        </div>
        {% if officer.bio %}<p>{{ officer.bio }}</p>{% endif %}
        {% if officer.email %}<p><a href="mailto:{{ officer.email }}">{{ officer.email }}</a></p>{% endif %}
      </article>
    {% endfor %}
  </div>
</section>

<section id="join" class="club-section">
  <h2>How to Join</h2>
  <div class="join-layout">
    <figure class="recruitment-poster">
      <img src="{{ '/assets/images/f26_recruitment.png' | relative_url }}" alt="Fall 2026 MKBC recruitment poster">
    </figure>
    <div class="join-cta">
      <h3>Membership Form</h3>
      <p>Submit the form to join MKBC and receive club updates from the officers.</p>
      <a class="btn btn--primary" href="https://forms.gle/jGPDGz8vXFUjM6E88">Open Membership Form</a>
    </div>
  </div>
</section>

<section id="policies" class="club-section">
  <h2>Policies</h2>
  <div class="club-grid">
    {% for item in site.data.policies %}
      <article class="club-card">
        <h3>{{ item.title }}</h3>
        {% if item.items %}
          <ul class="policy-list">
            {% for bullet in item.items %}
              <li>{{ bullet | markdownify | remove: '<p>' | remove: '</p>' }}</li>
            {% endfor %}
          </ul>
        {% else %}
          <p>{{ item.description }}</p>
        {% endif %}
      </article>
    {% endfor %}
  </div>
</section>

<section id="former-presidents" class="club-section">
  <h2>Former Presidents</h2>
  <div class="club-grid legacy-grid">
    {% for leader in site.data.past_presidents %}
      <article class="club-card legacy-card">
        <div class="officer-photo">
          {% if leader.image and leader.image != "" %}
            {% if leader.image contains "://" %}
              <img src="{{ leader.image }}" alt="{{ leader.name }}">
            {% else %}
              <img src="{{ leader.image | relative_url }}" alt="{{ leader.name }}">
            {% endif %}
          {% else %}
            <img src="{{ '/assets/images/officers/default-officer.svg' | relative_url }}" alt="">
          {% endif %}
        </div>
        <div>
          <h3>{{ leader.name }}</h3>
          <p class="club-card-meta">{{ leader.role }}</p>
        </div>
        {% if leader.note %}<p>{{ leader.note }}</p>{% endif %}
      </article>
    {% endfor %}
  </div>
</section>
