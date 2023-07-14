function setElementRequired(element, state) {
    element.required = state
    if (state) {
        if (element.labels[0].innerText.slice(-1) !== '*')
            element.labels[0].innerText += '*'
    } else {
        while (element.labels[0].innerText.slice(-1) === '*')
            element.labels[0].innerText = element.labels[0].innerText.slice(0, -1)
    }
}