""" Handle the request and attach the received client info to the returned page.
"""


import textwrap

html_template = """
<!DOCTYPE html>
<html>
<head>
<title>echo client hints on prerendering page</title>
</head>
<script src="/speculation-rules/prerender/resources/utils.js"></script>
<body>
<script>

// Allow generator to add the received CH information into this script.
%s
const params = new URLSearchParams(location.search);
const uid = params.get("uid");

function terminate_test(reason) {
    const bc = new PrerenderChannel('test-channel', uid);
    bc.postMessage({
        result: 'FAILED',
        'reason': reason
    });
    bc.close();
}

// Performs the following checks on prerendering pages:
// 1. The client did not send server_received_full_version_list when fetching
//    the prerendering main resource.
// 2. The request initiated by the prerendering page is sent with
//    sec-ch-ua-full-version-list attached, because the server asked the
//    prerendering page to attach this hint for the following requests.
// If any of the checks fails, it will ask the main test page to terminate
// the test.
// Otherwise, it asks the initiator page to perform activation, and informs
// the main test page of the test success upon being activated. This is used
// to verify that the initiator page's client hints cache is not modified by
// the prerendering page, i.e., the initiator page does not attach
// sec-ch-ua-full-version-list to the requests.
async function load_as_prerendering_page() {
    // The first prerendering request should not contain the field of
    // sec-ch-ua-full-version-list, as prerender is initiated by the initial
    // page.
    if (!server_received_bitness || server_received_full_version_list) {
        terminate_test(
            `Prerender page saw unexpected request headers.
            bitness: ${server_received_bitness},
            full_version: ${server_received_full_version}`
        );
    }
    const r = await fetch("../resources/echo-client-hints-received.py");

    if (r.status != 200 ||
        !r.headers.get('server_received_bitness', false) ||
        !r.headers.get('server_received_full_version_list', false)
    ) {
        terminate_test(
            `Prerender page saw unexpected headers while fetching
                sub-resources.
                bitness: ${r.headers.get('server_received_bitness')},
                full_version: ${r.headers.get('server_received_full_version_list')}`
        );
    } else {
        document.onprerenderingchange = () => {
            const bc = new PrerenderChannel('test-channel',
                uid);
            // Send the result to the test runner page.
            bc.postMessage({
                result: "PASSED"
            })
        };
        const bc = new PrerenderChannel('prerender-channel', uid);
        bc.postMessage("ready for activation");
    }
}

// Performs the check below on initiator pages:
// 1. The client did not send server_received_full_version_list when fetching
//    the initiator page.
// If the check fails, it will ask the main test page to terminate the test.
// Otherwise, it will:
// 1. Initiate a prerendering action. And the prerendering page will perform
//    some checks.
// 2. Wait for the prerendering page to pass all checks and send a signal back.
// 3. Activate the prerendered page.
async function load_as_initiator_page() {
    if (!server_received_bitness || server_received_full_version_list) {
        // The initial headers are not as expected. Terminate the test.
        terminate_test(
            `unexpected initial headers.
            bitness: ${server_received_bitness},
            full_version: ${server_received_full_version}`
        );
        return;
    }
    const prerendering_url = location.href + '&prerendering=true';

    // Waiting for the prerendered page to be ready for activation.
    const bc = new PrerenderChannel('prerender-channel', uid);
    const gotMessage = new Promise(resolve => {
        bc.addEventListener('message', e => {
            resolve(e.data);
        }, {
            once: true
        });
    });
    startPrerendering(prerendering_url);

    data = await gotMessage;
    if (data != 'ready for activation'){
        terminate_test(`Initial page received unexpected result: ${data}`);
    }else {
        window.location = prerendering_url;
    }
}

if (params.has('prerendering')) {
  load_as_prerendering_page();
} else {
  load_as_initiator_page();
}

</script>
</body>
</html>
"""

def translate_to_js(val: bool) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    return ""

def main(request, response):
    response.headers.append(b"Access-Control-Allow-Origin", b"*")
    response.headers.append(b"Access-Control-Allow-Headers", b"*")
    response.headers.append(b"Access-Control-Expose-Headers", b"*")

    if "prerendering=true" in request.url_parts.query:
        response.headers.set(b"Accept-CH", "sec-ch-ua-full-version-list")

    response.status = 200

    # This part is to check the sub-resources' headers.
    response.headers.set(
        b"server_received_bitness", b"sec-ch-ua-bitness" in request.headers
    )
    response.headers.set(
        b"server_received_full_version_list",
        b"sec-ch-ua-full-version-list" in request.headers
    )

    # Insert the received hints into script.
    content = html_template % (
        textwrap.dedent(
            f"""
            const server_received_bitness =
                {translate_to_js(b"sec-ch-ua-bitness" in request.headers)};
            const server_received_full_version_list =
                {translate_to_js(b"sec-ch-ua-full-version-list" in
                    request.headers)};
            """
        )
    )
    response.content = content.encode("utf-8")
