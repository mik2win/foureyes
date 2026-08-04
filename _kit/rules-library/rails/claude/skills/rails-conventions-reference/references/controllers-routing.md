# Controllers and routing

## Controllers

```ruby
# GOOD — thin controller
class RecordsController < ApplicationController
  def create
    @record = RecordCreator.new(current_user).call(record_params)
    if @record.persisted?
      redirect_to @record, notice: t('.success')
    else
      render :new, status: :unprocessable_entity
    end
  end
end

# BAD — business logic leaking into controller
def create
  @record = Record.new(record_params)
  @record.status = :draft
  @record.processed_at = nil
  RelatedModel.find_or_create_by(year: params[:year]).update(total: ...)
  @record.save
end
```

## Routing

```ruby
# RESTful resources — max 1 level nesting
resources :records, only: %i[index show] do
  resources :items, only: %i[index new create], shallow: true
end

# Use shallow nesting for cleaner URLs
resources :entries, shallow: true

# Named routes for readability
get '/dashboard', to: 'dashboard#index', as: :dashboard
```
