# UI/UX — worked examples

Companion reference to the `ui-ux` rule; loaded on demand.

Examples use **Slim** syntax.

---

## Partial vs ViewComponent vs Helper — Decision Guide

```slim
/ Helper — formatting only
= format_amount(record.total)
span class=status_badge_class(record.status)

/ Partial — reusable template, minimal logic
= render "shared/flash_messages"
= render "shared/stats_cards", stats: @stats
= render "records/row", record: record

/ ViewComponent — complex UI with logic or Stimulus
= render CardComponent.new(record: record, editable: current_user.admin?)
```

## Partials

```slim
/ BAD — business logic in partial
- delta = record.new_value - record.old_value
- css = delta > 0 ? "text-red-600" : "text-green-600"

/ GOOD — logic in helper, partial only renders
span class=delta_css_class(delta)
  = format_amount(delta)
```

## ViewComponent

```ruby
# app/components/card_component.rb
class CardComponent < ViewComponent::Base
  def initialize(record:, editable: false)
    @record = record
    @editable = editable
  end

  def status_class
    @record.active? ? "bg-green-50" : "bg-gray-50"
  end
end
```

```slim
/ app/components/card_component.html.slim
div class=status_class
  p = @record.title
  - if @editable
    = link_to "Edit", edit_record_path(@record)
```

## Helpers

Use for formatting and CSS class generation. Keep helpers focused; no business logic or DB queries:

```ruby
# app/helpers/application_helper.rb
def format_amount(value)
  number_with_delimiter(value, delimiter: " ")
end

def status_badge_class(status)
  status.to_sym == :active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
end

def delta_css_class(delta)
  delta.positive? ? "text-red-600" : "text-green-600"
end
```

Never put business logic in helpers. If you need to query the database or orchestrate objects — that belongs in a model or service.

## Hotwire — Turbo

**Turbo Frames** — scope partial updates:

```slim
= turbo_frame_tag "stats_summary" do
  = render "shared/stats_cards", stats: @stats

= turbo_frame_tag "filter_form" do
  = render "shared/filter_form", form: @filter
```

**Turbo Streams** — targeted DOM updates from the controller:

```ruby
# app/controllers/records_controller.rb
def create
  @record = RecordCreator.new(current_user).call(record_params)
  respond_to do |format|
    format.turbo_stream do
      render turbo_stream: [
        turbo_stream.prepend("records_list", partial: "records/row", locals: { record: @record }),
        turbo_stream.replace("stats_summary", partial: "shared/stats_cards", locals: { stats: recalc_stats })
      ]
    end
    format.html { redirect_to records_path }
  end
end
```

**Prefer native HTML** where possible:

```slim
/ GOOD — native dialog
dialog#confirm_dialog
  p Are you sure?
  button Confirm

/ GOOD — native details/summary for accordion
details
  summary Rate History
  = render "records/history", record: @record
```

## Stimulus

```javascript
// app/javascript/controllers/preview_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["input", "output"]

  update() {
    this.outputTarget.textContent = this.inputTarget.value
  }
}
```

```slim
div data-controller="preview"
  input type="text" data-preview-target="input" data-action="input->preview#update"
  span data-preview-target="output"
```

```javascript
// BAD — imperative, manual event binding
connect() {
  this.inputTarget.addEventListener('input', this.update.bind(this))
}
```

## TailwindCSS

```slim
/ GOOD
div.flex.items-center.justify-between.p-4.bg-white.border.rounded-lg

/ BAD
div style="display: flex; padding: 16px;"
```

```ruby
def card_classes
  "bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
end
```

## Flash Messages

Render flash in the layout via a shared partial; use a helper for CSS by type:

```slim
/ app/views/shared/_flash_messages.html.slim
- flash.each do |type, message|
  div class=flash_css_class(type)
    = message
```

## Server-Side Formatting

```slim
/ GOOD — formatted on server
span = format_amount(@total)
span data-value=@total data-formatted=format_amount(@total)

/ BAD — raw number only, formatting done in JS
span data-raw=@total
```
