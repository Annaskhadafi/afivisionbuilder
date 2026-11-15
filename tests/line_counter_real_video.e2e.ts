import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('real video produces detections, tracks and line-counter preview', async ({ app, browser }) => {
  const video = process.env.LINE_COUNTER_TEST_VIDEO;
  const model = process.env.LINE_COUNTER_TEST_MODEL;
  test.skip(!video || !model, 'Set LINE_COUNTER_TEST_VIDEO and LINE_COUNTER_TEST_MODEL');
  await app.open('/');
  const result = await browser.evaluate(async ({ video, model }) => {
    const workflow = { nodes: [
      {id:'input',type:'input',enabled:true,config:{sourceType:'video',filePath:video,loop:false,dropFrames:true,torchCpuThreads:2}},
      {id:'video_speed_controller',type:'video_speed_controller',enabled:true,config:{playbackSpeed:0.75,pause:false}},
      {id:'detector',type:'detector',enabled:true,config:{engine:'ultralytics_yolo',modelPath:model,customModelPath:model,threshold:0.45}},
      {id:'tracker',type:'tracker',enabled:true,config:{algorithm:'bytetrack',enableReid:true,reidDevice:'cpu',minimumConsecutiveFrames:1}},
      {id:'line_counter',type:'line_counter',enabled:true,config:{startPoint:'0.291,0.336',endPoint:'0.337,0.819',triggerAnchor:'center',showAnchor:true}},
      {id:'preview',type:'preview',enabled:true,config:{showLabels:true,showTrails:true}}
    ],edges:[['input','video_speed_controller'],['video_speed_controller','detector'],['detector','tracker'],['tracker','line_counter'],['line_counter','preview']]};
    const response = await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workflow})});
    return {status:response.status,body:await response.text()};
  }, {video, model});
  expect(result.status).toBe(200);
  await expect.poll(async () => browser.evaluate(async () => {
    const status = await (await fetch('/api/status')).json();
    if (status.error) throw new Error(status.error);
    return status.nodeTelemetry?.tracker?.itemCount || 0;
  }), {timeout:90000}).toBeGreaterThan(0);
  await expect.poll(async () => browser.evaluate(async () => {
    const status = await (await fetch('/api/status')).json();
    return status.nodeTelemetry?.line_counter?.itemCount || 0;
  }), {timeout:30000}).toBeGreaterThan(0);
  await expect.poll(async () => browser.evaluate(async () => {
    const status = await (await fetch('/api/status')).json();
    return status.nodeTelemetry?.preview?.itemCount || 0;
  }), {timeout:30000}).toBeGreaterThan(0);
  const firstPreviewTime = await browser.evaluate(async () => {
    const status = await (await fetch('/api/status')).json();
    return status.nodeTelemetry?.preview?.timestamp || 0;
  });
  await expect.poll(async () => browser.evaluate(async () => {
    const status = await (await fetch('/api/status')).json();
    return status.nodeTelemetry?.preview?.timestamp || 0;
  }), {timeout:30000}).toBeGreaterThan(firstPreviewTime);
  await app.open('/api/preview/preview');
  await app.screenshot('real-video-detection-tracking-centroid');
  await browser.evaluate(async () => { await fetch('/api/stop',{method:'POST'}); });
});
