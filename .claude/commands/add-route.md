Create a new Flask route and page template.

## Steps

### 1. Create the template
- Create `backend/templates/<page_name>.html`
- Extend `base.html`: `{% extends 'base.html' %}`
- Set title block: `{% block title %}<Page Title> - EstradaBot{% endblock %}`
- Add content in `{% block content %}...{% endblock %}`
- Use Bootstrap 5 classes and follow existing page patterns (cards, tables, icons from `bi-*`)

### 2. Add the route
- In `backend/app.py`, add:
  ```python
  @app.route('/<route-path>')
  @login_required
  def <route_function>():
      return render_template('<page_name>.html')
  ```
- Add role restrictions if needed (check `current_user.role`)

### 3. Add navigation link
- In `backend/templates/base.html`, add a sidebar nav link in the appropriate section:
  ```html
  <li class="nav-item">
      <a class="nav-link {% if request.endpoint == '<route_function>' %}active{% endif %}" href="{{ url_for('<route_function>') }}">
          <i class="bi bi-<icon-name>"></i> <Page Title>
      </a>
  </li>
  ```

## After creating

Report what was created and remind the developer to test the page loads at the new URL.

## Ask the developer

Before creating, confirm:
1. What is the page name and URL path?
2. What content should the page display?
3. Which roles should have access?
4. Where in the sidebar navigation should it appear?
