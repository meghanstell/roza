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
  outdir="/glade/derecho/scratch/meghan/Roza/froude/froude_hourly/"
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
  h_gmc=1000
  delta_hg=50

  ; Site Variables
  ; Site A
  SiteA_phi_deg=105.0
  SiteA_phi_rad=SiteA_phi_deg*(pi/180.)
  SiteA_height=1500.0
  ; Site B
  SiteB_phi_deg=120.0
  SiteB_phi_rad=SiteB_phi_deg*(pi/180.)
  SiteB_height=1500.0

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
    ter = a->Z(0,0,:,:)*1. ;wrf_user_getvar(a,"HGT",0)           ; Read the variable to memory
    index=ter
    index@_FillValue=-999.0
    
    ; Full level height in m
    hgtfull=1.*a->Z ;(wrf_user_getvar(a,"PHB",0)+wrf_user_getvar(a,"PH",0))/g
    hgt=rm_single_dims(hgtfull(:,:,:,:))
    
    ; ; Half level height (mass center)
    height=(hgt(1:mdims(1),:,:)+hgt(0:mdims(1)-1,:,:))*0.5 ;wrf_user_getvar(a,"height",0)
    height_agl=rm_single_dims(height)
    height_agl=0.
    dz=height_agl
    
    ; ; Variable used for interpolation (both AMSL and AGL)
    do k=0,mdims(1)-1
        height_agl(k,:,:)=height(k,:,:)-ter
        dz(k,:,:)=hgt(k+1,:,:)-hgt(k,:,:)
    end do

    index_hagl=where(height_agl.lt.h_gmc+delta_hg,1.,-999.)
    index_hagl@_FillValue=-999.

    ; hgt=1.*a->Z

    ; ; Half level height (mass center)
    ; height=(hgt(:,1:mdims(1),:,:)+hgt(:,0:mdims(1)-1,:,:))*0.5 ;wrf_user_getvar(a,"height",0)
    ; height_agl=rm_single_dims(height)
    ; height_agl=0.
    ; dz=height_agl

    ; ; Variable used for interpolation (both AMSL and AGL)
    ; do k=0,mdims(1)-1
    ;   height_agl(k,:,:)=height(k,:,:)-ter
    ;   dz(k,:,:)=hgt(k+1,:,:)-hgt(k,:,:)
    ; end do
    ; dz=rm_single_dims(dz)
    ; height_agl=rm_single_dims(height_agl)
    ; height=rm_single_dims(height)

    ; index_hagl=where(height_agl.lt.h_gmc+delta_hg,1.,-999.)
    ; index_hagl@_FillValue=-999.

    ; wind and instability
    u=wrf_user_getvar(a,"U",-1)
    v=wrf_user_getvar(a,"V",-1)
    uvmet=wrf_uvmet(u,v,lat,lon,cen_lon,cone)

    uafull=uvmet(0,:,:,:,:)
    vafull=uvmet(1,:,:,:,:)

    ua=uafull(0,:,:,:)
    va=vafull(0,:,:,:)
    delete(uvmet)
    delete(u)
	delete(v)
	delete(uafull)
	delete(vafull)

    ; uvmet=wrf_user_getvar(a,"uvmet",-1)
    ; ua=uvmet(0,:,:,:,:)
    ; va=uvmet(1,:,:,:,:)
    ; delete(uvmet)

    p=a->P(0,:,:,:) ;(0,:,:,:) ; total pressure
    tk=a->TK(0,:,:,:)
    th=tk*(100000./p)^0.286
    bn2_full=th

    tsk=b->T2(:,:,:)
    psfc=a->P(:,0,:,:)

    thz=hgt
    thz(0,:,:)=tsk*(100000./psfc)^0.286

    do k=1,mdims(1)-1
        thz(k,:,:)=(th(k,:,:)+th(k-1,:,:))*0.5
    end do

    ; BN2 ;undefined without a target range
    do k=0,mdims(1)-1
        bn2_full(k,:,:)=g/th(k,:,:)*(thz(k+1,:,:)-thz(k,:,:))/dz(k,:,:)
    end do
   
    bn2=dim_avg_n(index_hagl*bn2_full,0)

    ; Froude Site A
    ;    phi=105 deg -- SiteA_phi_rad
    ;    height=1500 -- SiteA_height
    fr_A = ter
	fr_A = 0.
	fr_A@_FillValue=-999.
	h_local_A=height_agl
	h_local_A=0.
	do k=0,mdims(1)-1
        h_local_A(k,:,:)=-(ter-SiteA_height) 
	end do
	index_ha=where(height_agl.lt.h_local_A,1.,-999.)
	index_ha@_FillValue=-999.
	u_a=dim_avg_n(index_ha*ua,0)
	v_a=dim_avg_n(index_ha*va,0)
	bn2_a=dim_avg_n(index_ha*bn2_full,0)
	bn2_a=where(bn2_a.eq.0.,-999.,bn2_a)
	bn2_a@_FillValue=-999.
	fr_A=((u_a*cos(SiteA_phi_rad)))+((v_a*sin(SiteA_phi_rad)))/(abs(bn2_a))^0.5/h_local_A(0,:,:)
	fr_A=where(fr_A.lt.10.,fr_A,10.)
    fr_A=where(bn2_a.lt.0,999.,fr_A)



    ; Froude Site B
    ;    phi=120 deg -- SiteB_phi_rad
    ;    height=1500 -- SiteB_height
    fr_B = ter
	fr_B = 0.
	fr_B@_FillValue=-999.
	h_local_B=height_agl
	h_local_B=0.
	do k=0,mdims(1)-1
        h_local_B(k,:,:)=-(ter-SiteB_height) 
	end do
	index_hb=where(height_agl.lt.h_local_B,1.,-999.)
	index_hb@_FillValue=-999.
	u_b=dim_avg_n(index_hb*ua,0)
	v_b=dim_avg_n(index_hb*va,0)
	bn2_b=dim_avg_n(index_hb*bn2_full,0)
	bn2_b=where(bn2_b.eq.0.,-999.,bn2_b)
	bn2_b@_FillValue=-999.
	fr_A=((u_b*cos(SiteB_phi_rad)))+((v_b*sin(SiteB_phi_rad)))/(abs(bn2_b))^0.5/h_local_B(0,:,:)
	fr_A=where(fr_B.lt.10.,fr_B,10.)
    fr_A=where(bn2_b.lt.0,999.,fr_B)


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

    dimNames = (/"Time", "south_north", "west_east"/)
    dimSizes = (/ 1 ,    131,  121 /)
    dimUnlim = (/ True , False, False/)
    filedimdef(outcdf, dimNames, dimSizes, dimUnlim)
    var_names = (/ "BN2",  "FrA","FrB" /)
    var_types = (/ "float", "float","float" /)
    filevardef(outcdf, var_names, var_types, dimNames)
    outcdf->Time=   (Time)
    outcdf->BN2=		(/reshape(bn2,(/1,131,121/))/)
    outcdf->FrA=		(/reshape(fr_A,(/1,131,121/))/)
    outcdf->FrB=		(/reshape(fr_B,(/1,131,121/))/)

    print( "Output Written to " + cf ) 
  end do
  print( "Done Processing " + year + "." + month ) 
end