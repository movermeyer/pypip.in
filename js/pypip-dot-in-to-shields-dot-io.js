ENDPOINT_CONVERSION = new Map([
    ["format", "format"],
    ["implementation", "implementation"],
    ["license", "l"],
    ["py_versions", "pyversions"],
    ["status", "status"],
    ["v", "v"],
    ["version", "v"],
    ["wheel", "wheel"]
]);

QUERY_PARAM_CONVERSION = new Map([
    ["text", "label"]
]);

PERIOD_PARAM_TO_ENDPOINT = new Map([
    ["day", "dd"],
    ["week", "dw"],
    ["month", "dm"],
]);

function handle_downloads_endpoint(url_params) {
    // Warning: mutates url_params
    var new_endpoint = "dm"
    if (url_params.has("period")) {
        new_endpoint = PERIOD_PARAM_TO_ENDPOINT.get(url_params.get("period")) || new_endpoint;
        url_params.delete("period");
    }
    return new_endpoint;
}

function convert_params(url_params) {
    // Warning: mutates url_params
    for (var pair of url_params.entries()) {
        if (QUERY_PARAM_CONVERSION.has(pair[0])) {
            url_params.set(QUERY_PARAM_CONVERSION.get(pair[0]), pair[1]);
        }
    }
}

function normalize_url(url) {
    return url.toLowerCase().replace(/^"/, '').replace(/"$/, '');
}

function pypip_dot_in_to_shields_dot_io(url) {
    url = normalize_url(url);
    var parser = document.createElement('a');
    parser.href = url;

    url_params = new URLSearchParams(parser.search);
    convert_params(url_params);

    var endpoint = parser.pathname.split('/')[1];
    var project = parser.pathname.split('/')[2];

    var is_download_count_badge = false;
    var is_egg_badge = endpoint === 'egg';

    if (endpoint === 'd' || endpoint === 'download') {
        shields_endpoint = handle_downloads_endpoint(url_params);
        is_download_count_badge = true;
    } else {
        shields_endpoint = ENDPOINT_CONVERSION.get(endpoint);
    }

    if (shields_endpoint === undefined) {
        result = null
    } else {
        result = `https://img.shields.io/pypi/${shields_endpoint}/${project}.svg${url_params.keys().next().done ? '' : '?' + url_params.toString()}`;
    }

    return [result, is_download_count_badge, is_egg_badge];
}

function go() {
    var results = pypip_dot_in_to_shields_dot_io(document.getElementById('pypip_url').value);
    var shields_dot_io_url = results[0];
    var is_download_count_badge = results[1]
    var is_egg_badge = results[2]

    document.getElementById('shieldsio_url').value = shields_dot_io_url !== null ? shields_dot_io_url : "";
    document.getElementById('preview').hidden = !(shields_dot_io_url !== null);
    var resulting_badge_link = document.getElementById('resulting_badge').href = shields_dot_io_url;
    var resulting_badge = document.getElementById('resulting_badge');
    resulting_badge.src = shields_dot_io_url;
    resulting_badge.hidden = !(shields_dot_io_url !== null);

    document.getElementById("egg_badge_warning").hidden = !is_egg_badge
    document.getElementById("failed_warning").hidden = !(shields_dot_io_url === null && !is_egg_badge)
    document.getElementById("download_badge_warning").hidden = !is_download_count_badge
}

function copy() {
    //https://stackoverflow.com/a/30810322
    var shieldsio_url_text_box = document.getElementById('shieldsio_url');
    shieldsio_url_text_box.select();

    var shieldsio_url_button = document.getElementById('copy_url_button');

    try {
        var successful = document.execCommand('copy');
        shieldsio_url_button.innerHTML = "Copied!"
    } catch (err) {
        shieldsio_url_button.innerHTML = "Unable to copy. Sorry!"
    }

}