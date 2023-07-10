function getDjangoUrl(id) {
    const urlSplit = window.location.href.split('/')
    const baseUrl = `${urlSplit[0]}//${urlSplit[2]}`
    const basePath = document.getElementById(id).getAttribute('data-url')
    return `${baseUrl}${basePath}`
}