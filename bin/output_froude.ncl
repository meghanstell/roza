;----------------------------------------------------------------------
; 
;
;  Project : Montana precipitation and cloud seedibility study 
;
;  Purpose :
;            This is an NCL file for preparing 700 hPa level data from 
;            CONUS404 run.
;
;  Remarks : 1) Froude number computation is set up for each
;				range differently becaues of
;               range height and orientation.
;            2) U and V are rotated appropriately.
;            3) Instead of reading RAINNC + I_RAINNC and SNOWNC, this code
;               reads PREC_ACC_NC and SNOW_ACC_NC (hourly accumulation
;               as oppose to accumulation from model init)
;
; Usage    : ncl 'year =2000 month=01' output_seedingcriteria_IDWR.ncl
;
; Original Code from Lulin.  Modified by Kyoko Ikeda 6 December 2017
; Modified for IDWR by Courtney Weeks 6 October 2021,
;Modified for Montana by Meghan Stell September 2024
;            
;----------------------------------------------------------------------

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

; calculate froude values
function calFroude(ter, height_agl, mdims, ua, va, bn2_full, phi)
  begin
    fr_Val = ter
    fr_Val = 0.
    fr_Val@_FillValue=-999.
    h_local_val=height_agl
    h_local_val=0.
    do k=0,mdims(1)-1
      h_local_val(k,:,:)=-(ter-3000.) 
    end do
    index_hval=where(height_agl.lt.h_local_val,1.,-999.)
    index_hval@_FillValue=-999.
    u_val=dim_avg_n(index_hval*ua,0)
    v_val=dim_avg_n(index_hval*va,0)
    bn2_val=dim_avg_n(index_hval*bn2_full,0)
    bn2_val=where(bn2_val.eq.0.,-999.,bn2_val)
    bn2_val@_FillValue=-999.
    fr_Val=(u_val*cos(phi)+v_val*sin(phi))/(abs(bn2_val))^0.5/h_local_val(0,:,:)
    fr_Val=where(fr_Val.lt.10.,fr_Val,10.)
    return fr_Val
  end



begin
  ;*********************************************************;
  ;                    static variables                     ;
  ;*********************************************************;
  indir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cut/"
  outdir="/glade/derecho/scratch/meghan/Roza/froude/"
  month = sprinti("%0.2i",mm)

  constfile="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cut/wrfconstants_usgs404_roza.nc"
  cffile=addfile(constfile,"r")
  lat=wrf_user_getvar(cffile,"XLAT",-1)
  lon=wrf_user_getvar(cffile,"XLONG",-1)
  ; cen_lon=-97.89999
  cen_lon=(max(lon) - min(lon))/2.
  cone=1.
  
  ; Coefficients for water saturation ratio and ice saturation ratio
  cst=(/.609868993E03,.499320233E02,.184672631E01,.402737184E-1,.565392987E-3,.521693933E-5,.307839583E-7,.105785160E-9,.161444444E-12/)

  ; Thermodynamic constants
  t0=273.16
  c_pd=1005.0
  m_air=0.0289644
  r_d=287.05
  r_gas=8.316963
  l_v=2.501e6
  l_s=2.834e6
  g=9.80665

  ; Pi; later would add phi for mtn ranges to calc Fr once we know what ranges to use
  pi=3.1415926535897932384626433   

  ; AGL levels for GS MC
  h_gmc=2000
  delta_hg=50

  ;*********************************************************;
  ;                    Algorithm                            ;
  ;*********************************************************;
  ; if(mm.gt.5.and.mm.lt.10)
  ;   exit()
  ; end if
  ; if(mm.gt.9)
  ;   year=year-1
  ; end if
  month=sprinti("%0.2i",mm)

  ; f3d=systemfunc("/bin/ls -1 " + indir + "wrf3d*_" + year + "-" + month + "*")
  f3d=systemfunc("/usr/bin/find " + indir + " -name 'wrf3d*_" + year + "-" + month + "*.nc'")

  nfile=dimsizes(f3d)-1
  if(nfile.eq.0) then
    continue
  end if

  do nf=0, nfile
    ; Open files for precipitation distraction
    af=f3d(nf)
    a = addfile(af,"r")
    ; bf = str_sub_str(af,"3d","2d")
    bf = str_sub_str(af,"/wrf3d","/2d/wrf2d")
    b = addfile(bf,"r")
    Time = a->XTIME;
    time_vec := cd_calendar( Time(0) , 0)

    ; Start time loop to calcualte all MC and DC in each record over the entire domain
    time_stamp := sprinti("%0.4i", tointeger(time_vec(0,0))) + "-" \
                + sprinti("%0.2i", tointeger(time_vec(0,1))) + "-" \
                + sprinti("%0.2i", tointeger(time_vec(0,2))) + "_" \
                + sprinti("%0.2i", tointeger(time_vec(0,3))) + "0000"

    print("Working on time: " + time_stamp )
    print( " wrf3d " + af )
    print( " ... processing " ) 
    print( " " ) 

    cf = outdir + "stability_"+ time_stamp +".nc"

    if (fileexists(cf)) then
      print("File exists. Next file ... ")
      continue
    end if

    ; mdims(0) = time, mdims(1) = z, mdims(2) = y, mdims(3) = x
    mdims = getfilevardimsizes(a,"QVAPOR") ; get some dimension sizes for the file
    ter = a->Z(:,0,:,:)*1.
    index=ter
    index@_FillValue=-999.0

    ; Full level height in m
    hgt=1.*a->Z

    ; Half level height (mass center)
    height=(hgt(:,1:mdims(1),:,:)+hgt(:,0:mdims(1)-1,:,:))*0.5 ;wrf_user_getvar(a,"height",0)
    height_agl=height
    height_agl=0.
    dz=height_agl

    ; Variable used for interpolation (both AMSL and AGL)
    do k=0,mdims(1)-1
      height_agl(:,k,:,:)=height(:,k,:,:)-ter
      dz(:,k,:,:)=hgt(:,k+1,:,:)-hgt(:,k,:,:)
    end do

    index_hagl=where(height_agl.lt.h_gmc+delta_hg,1.,-999.)
    index_hagl@_FillValue=-999.

    ; wind and instability
    u=wrf_user_getvar(a,"U",-1)
    v=wrf_user_getvar(a,"V",-1)
    uvmet=wrf_uvmet(u,v,lat,lon,cen_lon,cone)
    ;uvmet=wrf_user_getvar(a,"uvmet",-1)
    uafull=uvmet(0,:,:,:,:)
    vafull=uvmet(1,:,:,:,:)

    ua=uafull;(0,:,:,:)
    va=vafull;(0,:,:,:)

    delete(uvmet)

    ; uvmet=wrf_user_getvar(a,"uvmet",-1)
    ; ua=uvmet(0,:,:,:,:)
    ; va=uvmet(1,:,:,:,:)
    ; delete(uvmet)

    p=a->P
    tk=a->TK
    th=tk*(100000./p)^0.286
    bn2_full=th

    tsk=b->T2
    psfc=a->P(:,0,:,:)

    thz=hgt
    thz(:,0,:,:)=tsk*(100000./psfc)^0.286

    do k=1,mdims(1)-1
      thz(:,k,:,:)=(th(:,k,:,:)+th(:,k-1,:,:))*0.5
    end do

    ; BN2 ;undefined without a target range
    do k=0,mdims(1)-1
      bn2_full(:,k,:,:)=g/th(:,k,:,:)*(thz(:,k+1,:,:)-thz(:,k,:,:))/dz(:,k,:,:)
    end do
    
    bn2=dim_avg_n(index_hagl*bn2_full,1)

    phi_range=ispan(0,359,15)
    phi_size = dimsizes(phi_range)
    fr_full=new((/1,phi_size,mdims(2),mdims(3)/),float,-999.)
    fr_full!1 = "Phi"
    fr_full&Phi = phi_range
    
    ; fr_full@_FillValue=-999.

    fr = ter
    fr = 0.
    fr@_FillValue=-999.

    index_h=height_agl
    index_h=0.
    index_h@_FillValue=-999.

    h_local=height_agl
	  h_local=0.
    h_local@_FillValue=-999.

    do xx = 0,mdims(3)-1
      do yy = 0,mdims(2)-1
        ; print("(x, y): ("+xx+", "+yy+") / ("+(mdims(3)-1)+", "+(mdims(2)-1)+")")
        xx_swath_lo=max((/(xx-15),0/))
        xx_swath_hi=min((/(xx+15),mdims(3)-1/))
        yy_swath_hi=min((/(yy+30),mdims(2)-1/))
        local_max_=max(ter(:,yy:yy_swath_hi,xx_swath_lo:xx_swath_hi))
        do k=0,mdims(1)-1
          h_local(:,k,yy,xx)=-(ter(:,yy,xx)-local_max_) 
        end do
      end do ;;yy
    end do ;;xx

    do pp = 0, phi_size-1
      ; print("(pp): ("+pp+") / ("+(phi_size-1)+")")
      pp_rad=phi_range(pp)*(pi/180.)
      index_h=where(height_agl.lt.h_local,1.,-999.)
      u_local=dim_avg_n(index_h*ua,1)
      v_local=dim_avg_n(index_h*va,1)
      bn2_local=dim_avg_n(index_h*bn2_full,1)
      bn2_local=where(bn2_local.eq.0.,-999.,bn2_local)
      bn2_local@_FillValue=-999.
      h_local=where(h_local.eq.0.,-999.,h_local)
      fr=((u_local*cos(pp_rad)))+((v_local*sin(pp_rad)))/(abs(bn2_local))^0.5/h_local(:,0,:,:)
      fr=where(fr.lt.10.,fr,10.)
      fr=where(bn2.lt.0,999.,fr)
      ; print(fr)
      ; rv=fr(:,yy,xx)
      fr_full(0,pp,:,:)=(/fr/)
    end do ;;pp



    ; do xx = 0,mdims(3)-1
    ;   do yy = 0,mdims(2)-1
    ;     print("(x, y): ("+xx+", "+yy+") / ("+(mdims(3)-1)+", "+(mdims(2)-1)+")")
    ;     xx_swath_lo=max((/(xx-15),0/))
    ;     xx_swath_hi=min((/(xx+15),mdims(3)-1/))
    ;     yy_swath_hi=min((/(yy+30),mdims(2)-1/))
    ;     local_max_=max(ter(:,yy:yy_swath_hi,xx_swath_lo:xx_swath_hi))
    ;     do k=0,mdims(1)-1
    ;       h_local(:,k,:,:)=-(ter-local_max_) 
    ;     end do
    ;     do pp = 0, phi_size-1
    ;       pp_rad=phi_range(pp)*(pi/180.)
    ;       index_h=where(height_agl.lt.h_local,1.,-999.)
    ;       u_local=dim_avg_n(index_h*ua,1)
    ;       v_local=dim_avg_n(index_h*va,1)
    ;       bn2_local=dim_avg_n(index_h*bn2_full,1)
    ;       bn2_local=where(bn2_local.eq.0.,-999.,bn2_local)
    ;       bn2_local@_FillValue=-999.
    ;       h_local=where(h_local.eq.0.,-999.,h_local)
    ;       fr=((u_local*cos(pp_rad)))+((v_local*sin(pp_rad)))/(abs(bn2_local))^0.5/h_local(:,0,:,:)
    ;       fr=where(fr.lt.10.,fr,10.)
    ;       fr=where(bn2.lt.0,999.,fr)
    ;       rv=fr(0,yy,xx)
    ;       fr_full(0,pp,yy,xx)=(/rv/)
    ;     end do ;;pp
    ;   end do ;;yy
    ; end do ;;xx

    ; Delete height variables
    delete(th)
    delete(thz)
    delete(bn2_full)
    delete(ua)
    delete(va)
    delete(height)
    delete(height_agl)
    delete(dz)
    delete(index_hagl)

    outcdf=addfile(cf, "c")

    setfileoption(outcdf,"DefineMode",True)
    print("Output...")
    dimNames = (/"Time", "Phi",  "south_north", "west_east"/)
    dimSizes = (/ 1 ,       24,            131,        121 /)
    dimUnlim = (/ True , False,          False,       False/)
    filedimdef(outcdf, dimNames, dimSizes, dimUnlim)
    ; var_names = (/   "BN2", "FR"/)
    ; var_types = (/ "float", "float"/)
    var_names = (/"FR"/)
    var_types = (/"float"/)
    filevardef(outcdf, var_names, var_types, dimNames)
        outcdf->Time=   (Time)
        ; outcdf->Phi=    (/phi_range/)
        ; outcdf->BN2=		(/reshape(bn2,(/1,0,131,121/))/)
        ; outcdf->BN2=		(/bn2/)
        outcdf->FR=		  (/fr_full/)
        print( "Output Written to " + cf ) 

  end do
  print( "Done Processing " + year + "." + month ) 

end
