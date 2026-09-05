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
