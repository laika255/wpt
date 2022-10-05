// META: script=/resources/test-only-api.js
// META: script=resources/pressure-helpers.js

'use strict';

pressure_test(async (t, mockPressureService) => {
  const sampleRate = 1.0;
  const pressureChanges = await new Promise(resolve => {
    const observer_changes = [];
    let n = 0;
    const observer = new PressureObserver(changes => {
      observer_changes.push(changes);
      if (++n === 4)
        resolve(observer_changes);
    }, {sampleRate});
    observer.observe('cpu');
    mockPressureService.startPlatformCollector(
        sampleRate * 2,
        /*forceUpdate*/ true);
  });
  assert_equals(pressureChanges.length, 4);
  assert_less_than_equal(
      (1 / sampleRate),
      pressureChanges[1][0].time - pressureChanges[0][0].time);
  assert_less_than_equal(
      (1 / sampleRate),
      pressureChanges[2][0].time - pressureChanges[1][0].time);
  assert_less_than_equal(
      (1 / sampleRate),
      pressureChanges[3][0].time - pressureChanges[2][0].time);
}, 'Faster collector: Timestamp difference between two changes should be higher or equal to the observer sample rate');
