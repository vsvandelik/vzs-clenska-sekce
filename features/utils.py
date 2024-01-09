def extend_form_of_labels(form, form_labels):
    """
    Sets the labels of the form fields to the given values.

    :param form: The form to extend.
    :param form_labels: A dictionary of form fields and their labels.
    """

    if form_labels:
        for field, label in form_labels.items():
            if field in form.fields:
                form.fields[field].label = label

    return form
