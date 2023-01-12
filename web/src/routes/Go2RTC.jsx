import { useState, useRef, useCallback, useMemo } from 'preact/hooks';
const emptyObject = Object.freeze({});

export default function Go2RTC() {

  const [streamData, setStreamData] = useState({});

  const templates = [
    '<a href="stream.html?src={name}">stream</a>',
    '<a href="webrtc.html?src={name}">2-way-aud</a>',
    '<a href="api/stream.mp4?src={name}">mp4</a>',
    '<a href="api/stream.mjpeg?src={name}">mjpeg</a>',
    '<a href="api/streams?src={name}">info</a>',
    '<a href="#" data-name="{name}">delete</a>',
  ];

  const addStream = () => {
    const src = document.querySelector('#src');
    const url = new URL('go2rtc/api/streams', location.href);
    url.searchParams.set('src', src.value);
    fetch(url, { method: 'PUT' }).then(reload);
  };

  const selectStreams = () => {
    const url = new URL('stream.html', location.href);

    const streams = document.querySelectorAll('#streams input');
    streams.forEach((i) => {
      if (i.checked) url.searchParams.append('src', i.name);
    });

    if (!url.searchParams.has('src')) return;

    let mode = document.querySelectorAll('.controls input');
    mode = Array.from(mode).filter((i) => i.checked).map((i) => i.name).join(',');

    window.location.href = `${url}&mode=${mode}`;
  };

  const deleteStream = (ev) => {
    if (ev.target.innerText !== 'delete') return;

    ev.preventDefault();

    const url = new URL('go2rtc/api/streams', location.href);
    url.searchParams.set('src', ev.target.dataset.name);
    fetch(url, { method: 'DELETE' }).then(reload);
  };

  const reload = () => {
    const url = new URL('go2rtc/api/streams', location.href);
    fetch(url).then((r) => r.json()).then((data) => {
      setStreamData(data);
    });
  };

  useEffect(() => {
    reload();
    const editor = ace.edit('config', {
      useWorker: false,
      printMargin: false,
    });
    editor.session.setMode('ace/mode/yaml');
    editor.setTheme('ace/theme/github');

    const xhr = new XMLHttpRequest();
    xhr.open('GET', 'go2rtc/api/getConfig', true);
    xhr.onload = function () {
      if (xhr.status === 200) {
        editor.setValue(xhr.responseText);
      }
    };
    xhr.send();
  }, []);
 
  return (
    <div>
      <table id="streams">
        <thead>
          <tr>
            <th>Name</th>
            <th>Online</th>
            <th>Commands</th>
          </tr>
        </thead>
        <tbody onClick={deleteStream}>
          {Object.entries(streamData).map(([name, value]) => {
            const online = value ? value.length : 0;
            const links = templates.map((link) => link.replace('{name}', encodeURIComponent(name))).join(' ');
            return (
              <tr key={name} data-id={name}>
                <td>
                  <label htmlFor={name}>
                    <input type="checkbox" id={name} name={name} />
                    {name}
                  </label>
                </td>
                <td>{online}</td>
                <td>{links}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <button type="button" id="add" onClick={addStream}>Add</button>
      <div className="controls">
        <button type="button" onClick={selectStreams}>Select</button>
      </div>

    <AceEditor id="config" />
    <button type="button" id="save-button" onClick={handleSave}>
      Save
    </button>
  </div>
    );
}
  
