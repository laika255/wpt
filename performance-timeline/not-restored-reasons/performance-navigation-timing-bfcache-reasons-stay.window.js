// META: title=RemoteContextHelper navigation using BFCache
// META: script=../test-helper.js
// META: script=/common/dispatcher/dispatcher.js
// META: script=/common/get-host-info.sub.js
// META: script=/common/utils.js
// META: script=/html/browsers/browsing-the-web/remote-context-helper/respources/remote-context-helper.js
// META: script=/websockets/constants.sub.js

'use strict';

// Ensure that notRestoredReasons are only updated after non BFCache navigation.
promise_test(async t => {
  const rcHelper = new RemoteContextHelper();
  // Open a window with noopener so that BFCache will work.
  const rc1 = await rcHelper.addWindow(
      /*config=*/ null, /*options=*/ {features: 'noopener'});
  // await useWebSocket(rc1, SCHEME_DOMAIN_PORT);
  const domainPort = SCHEME_DOMAIN_PORT;
  await rc1.executeScript((domain) => {
    var ws = new WebSocket(domain + '/echo');
  }, [domainPort]);

  const rc1_url = await rc1.executeScript(() => {
    return location.href;
  });

  // Navigate away.
  const rc2 = await rc1.navigateToNew();

  // Navigate back.
  await rc2.historyBack();
  // Check the reported reasons.
  await assertNotRestoredReasonsEquals(
    rc1,
    /*blocked=*/true,
    /*url=*/rc1_url,
    /*src=*/ "",
    /*id=*/"",
    /*name=*/"",
    /*reasons=*/["WebSocket"],
    /*children=*/[]);

  await rc1.historyForward();
  await rc2.historyBack();
  // This time no blocking feature is used, so the page is restored
  // from BFCache. Ensure that the previous reasons stay there.
  await assertNotRestoredReasonsEquals(
    rc1,
    /*blocked=*/true,
    /*url=*/rc1_url,
    /*src=*/ "",
    /*id=*/"",
    /*name=*/"",
    /*reasons=*/["WebSocket"],
    /*children=*/[]);
  });
