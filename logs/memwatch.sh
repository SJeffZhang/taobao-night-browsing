#!/bin/zsh
# Log memory of the Causal Forest run every 30 s until it exits. Read-only: never kills anything.
PID=$1
OUT=${0:h}/memwatch_cf.log
echo "time,footprint_gb,rss_gb,swap_used_mb,swap_free_mb,free_pct,cpu_pct" > $OUT
while kill -0 $PID 2>/dev/null; do
  fp=$(footprint -p $PID 2>/dev/null | awk '/Footprint:/{for(i=1;i<=NF;i++) if($i=="Footprint:"){v=$(i+1); u=$(i+2)}; if(u=="MB") v=v/1024; if(u=="KB") v=v/1048576; print v; exit}')
  rss=$(ps -o rss= -p $PID | awk '{printf "%.1f", $1/1048576}')
  cpu=$(ps -o pcpu= -p $PID | tr -d ' ')
  sw=$(sysctl -n vm.swapusage | awk '{gsub("M","",$6); gsub("M","",$9); print $6","$9}')
  fr=$(memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{gsub("%","",$2); print $2}')
  echo "$(date +%H:%M:%S),$fp,$rss,$sw,$fr,$cpu" >> $OUT
  sleep 30
done
echo "$(date +%H:%M:%S),process_exited" >> $OUT
