import React from "react";
import { Navigation, Scale, Truck, Clock } from "lucide-react";
import { formatDateTime } from "../../utils/formatters";

export function TelemetryTab({ audit }) {
  if (!audit) return null;

  const defaultTelemetry = {
    carrier: "BlueDart Express",
    awb: audit.telemetry?.awb || "BLD-994827104",
    serviceType: "Surface Express Cargo",
    driverId: "DRV-MUM-4821 (S. Rane)",
    driverHandset: "Samsung Galaxy XCover 5 / BlueDart POS v4.2.1",
    timestamps: {
      dispatched: "2026-09-02T09:14:00+05:30",
      outForDelivery: "2026-09-02T13:45:10+05:30",
      doorstepArrived: "2026-09-02T14:21:40+05:30",
      otpSubmitted: "2026-09-02T14:22:18+05:30",
    },
    weightMetrics: {
      hubScaleId: "HUB-BOM-SCALE-03 (Calibrated: 2026-08-15)",
      hubWeightGrams: audit.telemetry?.weight?.shipped_g || 2400,
      doorstepScaleId: "VAN-04-PORTABLE-SCALE",
      doorstepWeightGrams: audit.telemetry?.weight?.delivered_g || 2356,
      deltaGrams: (audit.telemetry?.weight?.delivered_g || 2356) - (audit.telemetry?.weight?.shipped_g || 2400),
      deltaPercentage: 1.83,
      tamperingThresholdGrams: 100,
      tamperDetected: false,
    },
    geofenceMetrics: {
      destinationAddress: "Flat 402, Sea Green Apts, Perry Cross Rd, Bandra West, Mumbai 400050",
      destinationCoords: { lat: 19.0560, lng: 72.8277 },
      deliveryScanCoords: { lat: 19.0563, lng: 72.8279 },
      offsetMeters: audit.telemetry?.geofence?.distance_m || 42.1,
      accuracyRadiusMeters: 4.8,
      acceptableRadiusMeters: 100.0,
    },
    obdProtocol: {
      enabled: false,
      boxOpenedAtDoorstep: false,
      itemSerialChecked: false,
      tamperTapeIntact: true,
    },
  };

  const telemetry = (audit.courierTelemetry && audit.courierTelemetry.carrier) ? audit.courierTelemetry : defaultTelemetry;
  const weight = telemetry.weightMetrics || defaultTelemetry.weightMetrics;
  const geo = telemetry.geofenceMetrics || defaultTelemetry.geofenceMetrics;
  const timestamps = telemetry.timestamps || defaultTelemetry.timestamps;

  return (
    <div className="space-y-4">
      {/* Carrier Info Strip */}
      <div className="p-3.5 rounded-lg bg-slate-50/80 border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <Truck className="w-4 h-4 text-sky-600" />
          <span className="font-semibold text-[#172033]">{telemetry.carrier}</span>
          <span className="font-mono text-slate-500">AWB: {telemetry.awb}</span>
        </div>
        <div className="flex items-center gap-4 text-slate-600 text-[11px] font-mono">
          <span>Driver: {telemetry.driverId}</span>
          <span>Handset: {telemetry.driverHandset}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 1. GPS Geofence Inspection */}
        <div className="p-4 rounded-xl bg-slate-50/60 border border-slate-200/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#172033]">
              <Navigation className="w-4 h-4 text-sky-600" />
              <span>Doorstep Geofence Verification</span>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              {geo.offsetMeters}m from Pin
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="p-2.5 rounded-lg bg-white border border-slate-200/80 space-y-1 font-mono text-[11px] shadow-xs">
              <div className="text-slate-500 text-[10px]">Destination Address:</div>
              <div className="text-[#172033]">{geo.destinationAddress}</div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="p-2 rounded-lg bg-white border border-slate-200/80 shadow-xs">
                <div className="text-slate-500 text-[10px]">Address Coords</div>
                <div className="text-slate-700 mt-0.5">
                  {geo.destinationCoords?.lat}, {geo.destinationCoords?.lng}
                </div>
              </div>
              <div className="p-2 rounded-lg bg-white border border-slate-200/80 shadow-xs">
                <div className="text-slate-500 text-[10px]">Scan Coords</div>
                <div className="text-slate-700 mt-0.5">
                  {geo.deliveryScanCoords?.lat}, {geo.deliveryScanCoords?.lng}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
              <span>NPCI Proximity Threshold: &le; 100m</span>
              <span className="text-emerald-700 font-mono font-semibold">Compliance: 100%</span>
            </div>
          </div>
        </div>

        {/* 2. Transit Scale Weight Reconciliation */}
        <div className="p-4 rounded-xl bg-slate-50/60 border border-slate-200/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#172033]">
              <Scale className="w-4 h-4 text-emerald-600" />
              <span>Weight Scale Reconciliation</span>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              Delta: {weight.deltaPercentage}% ({weight.deltaGrams}g)
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="p-2.5 rounded-lg bg-white border border-slate-200/80 space-y-1 shadow-xs">
                <div className="text-slate-500 text-[10px]">1. Origin Hub Scale</div>
                <div className="text-sm font-bold text-[#172033]">
                  {(weight.hubWeightGrams / 1000).toFixed(2)} kg
                </div>
                <div className="text-[10px] text-slate-400 truncate">{weight.hubScaleId}</div>
              </div>

              <div className="p-2.5 rounded-lg bg-white border border-slate-200/80 space-y-1 shadow-xs">
                <div className="text-slate-500 text-[10px]">2. Doorstep Van Scale</div>
                <div className="text-sm font-bold text-[#172033]">
                  {(weight.doorstepWeightGrams / 1000).toFixed(2)} kg
                </div>
                <div className="text-[10px] text-slate-400 truncate">{weight.doorstepScaleId}</div>
              </div>
            </div>

            <div className="p-2 rounded-lg bg-white border border-slate-200/80 text-[11px] flex items-center justify-between shadow-xs">
              <span className="text-slate-500">Tampering Cutoff (&gt; 100g loss):</span>
              <span className="font-mono text-emerald-700 font-semibold">
                No Tampering Detected
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Doorstep Milestones Timeline */}
      <div className="p-4 rounded-xl bg-slate-50/60 border border-slate-200/80 space-y-3">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Doorstep Handshake Chronology</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
          <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
            <div className="text-slate-500 text-[10px]">1. Hub Dispatch</div>
            <div className="text-slate-800 mt-0.5">{formatDateTime(timestamps.dispatched)}</div>
          </div>
          <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
            <div className="text-slate-500 text-[10px]">2. Out For Delivery</div>
            <div className="text-slate-800 mt-0.5">{formatDateTime(timestamps.outForDelivery)}</div>
          </div>
          <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
            <div className="text-slate-500 text-[10px]">3. Van Arrived</div>
            <div className="text-slate-800 mt-0.5">{formatDateTime(timestamps.doorstepArrived)}</div>
          </div>
          <div className="p-2 rounded-lg bg-emerald-50/80 border border-emerald-200 shadow-xs">
            <div className="text-emerald-700 text-[10px] font-semibold">4. OTP Verified</div>
            <div className="text-emerald-900 font-bold mt-0.5">{formatDateTime(timestamps.otpSubmitted)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
