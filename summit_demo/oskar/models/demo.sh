rm -r aa1-1m-* demo*image demo*fits ;
for f in demo-?.ini ;
  do oskar_sim_interferometer $f ;
done;
for f in aa1-1m-?.vis ;
  do  oskar_vis_to_ms $f -o $f.ms ;
done ;
for n in 1 2 3 4 ;
  do oskar_imager demo-im-$n.ini  ;
done

