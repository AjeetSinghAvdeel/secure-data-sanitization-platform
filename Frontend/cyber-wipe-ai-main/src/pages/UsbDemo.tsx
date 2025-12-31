import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";

type Device = {
  device: string;
  mountpoint: string;
  fstype?: string;
  total?: number;
  free?: number;
};

type DeletedFile = {
  name: string;
  path: string;
  inode: number;
  size: number;
  deleted: boolean;
};

const API_BASE = "http://localhost:5001";

const fmtBytes = (n?: number) => {
  if (n == null) return "-";
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  if (n === 0) return "0 B";
  const i = Math.floor(Math.log(n) / Math.log(1024));
  return `${(n / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
};

export default function UsbDemo() {
  const [loading, setLoading] = useState(false);
  const [admin, setAdmin] = useState<boolean>(false);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [files, setFiles] = useState<DeletedFile[]>([]);
  const [scanInFlight, setScanInFlight] = useState(false);
  const [recoverInFlight, setRecoverInFlight] = useState<number | null>(null);
  const [confirmAction, setConfirmAction] = useState(false);
  const [message, setMessage] = useState<string>("");

  const selectedDevice = useMemo(() => devices.find(d => (d.mountpoint === selected || d.device === selected)), [devices, selected]);

  const refreshDevices = async () => {
    setLoading(true);
    setMessage("");
    try {
      const res = await axios.get(`${API_BASE}/usb/devices`);
      setDevices(res.data.devices || []);
      setAdmin(!!res.data.admin);
      if ((res.data.devices || []).length && !selected) {
        setSelected(res.data.devices[0].mountpoint || res.data.devices[0].device);
      }
    } catch (e: any) {
      setMessage(e?.response?.data?.error || e.message || "Failed to load devices");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshDevices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const scan = async () => {
    if (!selected) return;
    setScanInFlight(true);
    setFiles([]);
    setMessage("");
    try {
      const res = await axios.post(`${API_BASE}/usb/scan`, { mountpoint: selected, device: selected }, { timeout: 120000 });
      setFiles(res.data.files || []);
      setMessage(`Found ${res.data.count ?? (res.data.files?.length || 0)} deleted files (showing up to 200).`);
    } catch (e: any) {
      setMessage(e?.response?.data?.error || e.message || "Scan failed");
    } finally {
      setScanInFlight(false);
    }
  };

  const recover = async (file: DeletedFile) => {
    if (!selected) return;
    if (!confirmAction) {
      setMessage("Recovery requires confirm to be checked.");
      return;
    }
    const inode = file.inode;
    setRecoverInFlight(inode);
    setMessage("");
    try {
      // Build a suggested filename from the original name if available
      const safeName = (file.name && file.name.trim().length > 0 ? file.name : `recovered_${inode}.bin`).replace(/[^A-Za-z0-9._-]+/g, "_");
      const res = await axios.post(`${API_BASE}/usb/recover_stream`, { device: selected, inode, filename: safeName }, { responseType: "blob" });
      const blob = new Blob([res.data], { type: res.headers['content-type'] || 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = safeName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setMessage(`Downloaded recovered file: ${safeName}`);
    } catch (e: any) {
      setMessage(e?.response?.data?.error || e.message || "Recovery failed");
    } finally {
      setRecoverInFlight(null);
    }
  };

  

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">USB Demo</h1>
      <p className="text-sm text-red-600 mb-4">Warning: Recovery and Secure Wipe are destructive/sensitive operations. Admin required. Check Confirm to proceed.</p>

      <div className="flex items-center gap-3 mb-4">
        <button className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-50" onClick={refreshDevices} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh Devices"}
        </button>
        <span className={`text-xs px-2 py-1 rounded ${admin ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}`}>
          Admin: {admin ? "Yes" : "No"}
        </span>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={confirmAction} onChange={e => setConfirmAction(e.target.checked)} />
          Confirm
        </label>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="col-span-1 border rounded p-4">
          <h2 className="font-semibold mb-3">Devices</h2>
          {devices.length === 0 && <div className="text-sm text-muted-foreground">No removable devices detected.</div>}
          <ul className="space-y-2 max-h-64 overflow-auto">
            {devices.map((d) => (
              <li key={d.mountpoint + d.device} className={`p-2 rounded border cursor-pointer ${selected === (d.mountpoint || d.device) ? "border-blue-500 bg-blue-50" : "border-gray-200"}`} onClick={() => setSelected(d.mountpoint || d.device)}>
                <div className="text-sm font-medium">{d.mountpoint} ({d.device})</div>
                <div className="text-xs text-gray-600">{d.fstype || "fs"} | Total {fmtBytes(d.total)} | Free {fmtBytes(d.free)}</div>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex gap-2">
            <button className="px-3 py-2 rounded bg-indigo-600 text-white disabled:opacity-50" onClick={scan} disabled={!selected || scanInFlight}>
              {scanInFlight ? "Scanning..." : "Scan Deleted Files"}
            </button>
          </div>
        </div>

        <div className="col-span-2 border rounded p-4">
          <h2 className="font-semibold mb-3">Deleted Files</h2>
          {files.length === 0 && <div className="text-sm text-muted-foreground">No results yet. Click Scan.</div>}
          <div className="max-h-80 overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2 pr-2">Name</th>
                  <th className="py-2 pr-2">Inode</th>
                  <th className="py-2 pr-2">Size</th>
                  <th className="py-2 pr-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {files.map((f) => (
                  <tr key={f.inode} className="border-b">
                    <td className="py-2 pr-2">{f.name}</td>
                    <td className="py-2 pr-2">{f.inode}</td>
                    <td className="py-2 pr-2">{fmtBytes(f.size)}</td>
                    <td className="py-2 pr-2">
                      <button className="px-2 py-1 rounded bg-emerald-600 text-white disabled:opacity-50" onClick={() => recover(f)} disabled={recoverInFlight === f.inode}>
                        {recoverInFlight === f.inode ? "Recovering..." : "Recover"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          
        </div>
      </div>

      {message && (
        <div className="mt-4 p-3 rounded border bg-gray-50 text-sm whitespace-pre-wrap">{message}</div>
      )}
    </div>
  );
}
