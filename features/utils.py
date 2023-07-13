def extend_form_of_labels(form, form_labels):
    if form_labels:
        for field, label in form_labels.items():
            if field in form.fields:
                form.fields[field].label = label

    return form
