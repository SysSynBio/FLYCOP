#!/usr/bin/python

# Example: >>%run synKtPHAFLYCOP
#          >>avgfitness,sdfitness=synKtPHAFLYCOP_oneConf(30,3.5,0.1,18)
# Goal: individual test to improve consortium {S.elongatus-P.putida}, depending on percentage of sucrose S.elongatus secretes, initial biomasses and NH4 in the medium.
# Run through the function synKtPHAFLYCOP_oneConf


import cobra
import pandas as pd
import tabulate
import re
import sys
import getopt
import os.path
import copy
import csv
import math
import cobra.flux_analysis.variability
import massedit
import subprocess
import shutil, errno
import statistics
import gurobipy
import optlang
from cobra import Reaction
from cobra import Metabolite


################################################################
### FUNCTION initialize_models #################################    
def initialize_models():
 # Only to run 1st time, to build the models!!
 if not(os.path.exists('ModelsInput/iJB785.mat')) or not(os.path.exists('ModelsInput/iJN1411.mat')):
     print('ERROR! Not iJB785.mat or iJN1411.mat files with GEM of consortium strains in ModelsInput!')
 else:
  path=os.getcwd()
  os.chdir('ModelsInput')
  # Synecho
  model=cobra.io.load_matlab_model('iJB785.mat')
  # Centralizing light intake: only 2 photon exchange opened
  model.reactions.get_by_id('EX_photon410(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon430(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon450(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon470(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon490(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon510(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon530(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon550(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon570(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon590(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon610(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon630(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon690(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_photon650(e)').lower_bound=-60
  model.reactions.get_by_id('EX_photon670(e)').lower_bound=-60
  # Updates for secreting sucrose are dynamic
  cobra.io.save_matlab_model(model,"iSynecho_cscBandSPS_over.mat",'model')

  # P.putida model for taking sucrose, not taking NO3 and generating PHA
  # Load iJN1411 Pputida model
  model=cobra.io.load_matlab_model('iJN1411.mat') 
  # 1.- PHA symplification plasmid elimination.
  # 1.1.- A single R-hydroxyacid is allowed as intermediate for PHA. PHA is allowed only in the most common form: 'PHAP2C80' (not included in the next list)
  for rxnID in ['PHAP2C120','PHAP2C121','PHAP2C121d6','PHAP2C140','PHAP2C141','PHAP2C141d5','PHAP2C142','PHAPCP100','PHAPCP40','PHAPCP60','PHAPCP70','PHAPCP80','PHAPCP90','PHAP2C101','PHAPC40','PHAPC70','PHAPC90','PHAPCT40','PHAPCT60','PHAP2C100','PHAP2C60','PHAPC50','PHAPCP50']:
      model.reactions.get_by_id(rxnID).bounds=(0,0)
  # 1.2.- R-hydroxyacid secretion not allowed.
  for rxnID in ['RHA100tpp','RHA101tpp','RHA120tpp','RHA121d6tpp','RHA121tpp','RHA140tpp','RHA141d5tpp','RHA141tpp','RHA142tpp','RHA160tpp','RHA40tpp','RHA50tpp','RHA60tpp','RHA70tpp','RHA80tpp','RHA90tpp','RHAP100tpp','RHAP40tpp','RHAP50tpp','RHAP60tpp','RHAP70tpp','RHAP80tpp','RHAP90tpp','RHAT40tpp','RHAT60tpp']:
      model.reactions.get_by_id(rxnID).bounds=(0,0)
  # 1.3.- Add transporter and Exchange reaction for the selected PHA 
  # PHA allowed: C80a. tpp + EX rather than DM_C80aPHA, due to COMETS takes it as metabolite in the media; although physiologically it is accumulated. It is just for modeling reasons.
  # Create the new metabolites
  c80apha_p = Metabolite('C80aPHA[p]', formula='C8H15O3R', name='C80_Medium_chain_length_aliphatic_Polyhydroxyalkanoate_p')
  c80apha_e = Metabolite('C80aPHA[e]', formula='C8H15O3R', name='C80_Medium_chain_length_aliphatic_Polyhydroxyalkanoate_e')
  reaction=Reaction('C80aPHAtpp')
  reaction.name='C80aPHA transporter periplasm'
  reaction.lower_bound=0
  reaction.upper_bound=1000
  reaction.reversibility=False
  reaction.objective_coefficient=0
  model.add_reaction(reaction)
  reaction.add_metabolites({'C80aPHA[c]':-1.0, c80apha_p:1.0})
  reaction.reaction='C80aPHA[c] --> C80aPHA[p]'
  del(reaction)
  reaction=Reaction('C80aPHAtex')
  reaction.name='C80aPHA transporter extracellular'
  reaction.lower_bound=0
  reaction.upper_bound=1000
  reaction.reversibility=False
  reaction.objective_coefficient=0
  model.add_reaction(reaction)
  reaction.add_metabolites({c80apha_p:-1.0, c80apha_e:1.0})
  reaction.reaction='C80aPHA[p] --> C80aPHA[e]'
  del(reaction)
  reaction=Reaction('EX_C80aPHA(e)')
  reaction.name='C80aPHA exchange'
  reaction.lower_bound=0
  reaction.upper_bound=1000
  reaction.reversibility=True
  reaction.objective_coefficient=0
  model.add_reaction(reaction)
  reaction.add_metabolites({c80apha_e:-1.0})
  reaction.reaction='C80aPHA[e] <=>'
  
  # 2.- Add reactions to allow taking sucrose as carbon source
  sucr_c = Metabolite('sucr[c]', formula='C12H22O11', name='sucrose_c')
  sucr_p = Metabolite('sucr[p]', formula='C12H22O11', name='sucrose_p')
  sucr_e = Metabolite('sucr[e]', formula='C12H22O11', name='sucrose_e')
  fru_c = Metabolite('fru[c]', formula='C6H12O6', name='fructose_c')
  del(reaction)
  reaction=Reaction('EX_sucr(e)')
  reaction.name='Sucrose exchange'
  reaction.lower_bound=0
  reaction.upper_bound=1000
  reaction.reversibility=True
  reaction.objective_coefficient=0
  model.add_reaction(reaction)
  reaction.add_metabolites({sucr_e:-1.0})
  reaction.reaction='sucr[e] <=>'
  del(reaction)
  reaction=Reaction('SUCRtex')
  reaction.name='sucrose transport via diffusion (extracellular to periplasm)'
  reaction.lower_bound=0
  reaction.upper_bound=1000
  reaction.reversibility=True
  reaction.objective_coefficient=0
  model.add_reaction(reaction)
  reaction.add_metabolites({sucr_e:-1.0, sucr_p:1.0})
  reaction.reaction='sucr[e] -> sucr[p]'
  del(reaction)
  reaction=Reaction('SUCRtpp')
  reaction.name='Sucrose transport via proton symport periplasm'
  reaction.lower_bound=0
  reaction.upper_bound=1000
  reaction.reversibility=False
  reaction.objective_coefficient=0
  model.add_reaction(reaction)
  reaction.add_metabolites({sucr_p:-1.0, 'h[p]':-1.0, sucr_c:1.0, 'h[c]':1.0})
  reaction.reaction='sucr[p] + h[p] -> sucr[c] + h[c]'
  del(reaction)
  reaction=Reaction('INVERTASE')
  reaction.name='Invertase'
  reaction.lower_bound=0
  reaction.upper_bound=1000
  reaction.reversibility=True
  reaction.objective_coefficient=0
  model.add_reaction(reaction)
  reaction.add_metabolites({sucr_c:-1.0, 'h2o[c]':-1.0, 'glc_D[c]':1.0, fru_c:1.0})
  reaction.reaction='sucr[c] + h2o[c] -> glc_D[c] + fru[c]'
  del(reaction)
  reaction=Reaction('FRUtpp')
  reaction.name='Fructose transport (cytoplasm to periplasm)'
  reaction.lower_bound=-1000
  reaction.upper_bound=1000
  reaction.reversibility=True
  reaction.objective_coefficient=0
  model.add_reaction(reaction)
  reaction.add_metabolites({'fru[p]':-1.0, fru_c:1.0})
  reaction.reaction='fru[p] <=> fru[c]'

  # 3.- Remove reactions to avoid NO3 intake (nitrate reductase NADH, corresponding to gens PP_1703 (NTRARx), PP_1705-PP_1706 (NTRIR2x))
  model.reactions.get_by_id('NTRARx').bounds=(0,0)
  model.reactions.get_by_id('NTRIR2x').bounds=(0,0)

  # 4.- Put sucrose as carbon source and adjust o2
  model.reactions.get_by_id('EX_o2(e)').bounds=(-18,1000)
  model.reactions.get_by_id('EX_glc(e)').bounds=(0,1000)
  model.reactions.get_by_id('EX_sucr(e)').bounds=(-3.1,0) # 3.1 as the equivalent to glucose=6.3
  model.reactions.get_by_id('SUCRtex').bounds=(3.1,3.1) # Because EX_sucr=(-3.1,-3.1) doesn't work in COMETS (give error GRV.5000).
  model.reactions.get_by_id('EX_pi(e)').bounds=(-0.6,1000)

  # 5.- Because of physiologically P.putida KT 2440 does not secrete other products under nitrogen limiting and in excess carbon source conditions, we restrict other subproducts metabolite secretion (except to gluconate) to allow the known behaviour of producing PHA.
  model.reactions.get_by_id('EX_glcn(e)').bounds=(0,1.2) # It is physiologically known that KT could secrete gluconate under those conditions
  model.reactions.get_by_id('EX_etoh(e)').bounds=(0,0) 
  model.reactions.get_by_id('EX_lac_D(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_acald(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_pyr(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_glc(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_ac(e)').bounds=(0,0)
  model.reactions.get_by_id('EX_algac_M_(e)').bounds=(0,0)

  # Save the model
  cobra.io.save_matlab_model(model, "iJN1411_sucr_notNO3_PHA.mat")
  del(model)
  os.chdir(path)
# end-def initialize_models
################################################################    


################################################################    
### FUNCTION mat_to_comets #####################################    
# mat_to_comets(modelPath)
def mat_to_comets(matInputFile):
    model=cobra.io.load_matlab_model(matInputFile)
    # Open output file:
    with open(matInputFile+'.cmt', mode='w') as f:
        # Print the S matrix
        f.write("SMATRIX  "+str(len(model.metabolites))+"  "+str(len(model.reactions))+"\n")
        for x in range(len(model.metabolites)):
            for y in range(len(model.reactions)):
                if (model.metabolites[x] in model.reactions[y].metabolites):
                    coeff=model.reactions[y].get_coefficient(model.metabolites[x])
                    f.write("    "+str(x+1)+"   "+str(y+1)+"   "+str(coeff)+"\n")
        f.write("//\n")
        
        # Print the bounds
        f.write("BOUNDS  -1000  1000\n");
        for y in range(len(model.reactions)):
            lb=model.reactions[y].lower_bound
            up=model.reactions[y].upper_bound
            f.write("    "+str(y+1)+"   "+str(lb)+"   "+str(up)+"\n")
        f.write("//\n")
        
        # Print the objective reaction
        f.write('OBJECTIVE\n')
        for y in range(len(model.reactions)):
            if (model.reactions[y] in model.objective):
                indexObj=y+1
        f.write("    "+str(indexObj)+"\n")
        f.write("//\n")
        
        # Print metabolite names
        f.write("METABOLITE_NAMES\n")
        for x in range(len(model.metabolites)):
            f.write("    "+model.metabolites[x].id+"\n")
        f.write("//\n")

        # Print reaction names
        f.write("REACTION_NAMES\n")
        for y in range(len(model.reactions)):
            f.write("    "+model.reactions[y].id+"\n")
        f.write("//\n")

        # Print exchange reactions
        f.write("EXCHANGE_REACTIONS\n")
        for y in range(len(model.reactions)):
            if (model.reactions[y].id.find('EX_')==0):
                f.write(" "+str(y+1))
        f.write("\n//\n")                
### end-function-mat_to_comets    
################################################################


################################################################
### FUNCTION synKtPHAFLYCOP_oneConf ############################
# maxCycles2=1000,500 or -1 meaning when so4, no3 or pi is exhausted.
def synKtPHAFLYCOP_oneConf(sucrPer=30,biomassSynecho=3.5,biomassKT=0.1,nh4=18,fitFunc='MaxPHA',maxCycles=1000,dirPlot='',repeat=3):
  '''
  Call: avgFitness, sdFitness = cleaning_oneConf(sucrPer,biomassSynecho,biomassKT,nh4)

  INPUTS: sucrPer: %sucrose (in function of carbon source)
          biomassSynecho: Initial biomass synecho
          biomassKT: Initial biomass putida (or ratio among both)
          nh4: initial NH4 in the media
          fitFunc: fitness function to optimize.
          maxCycles: cycles in COMETS run.
          dirPlot: copy of the graphs with several run results.
          repeat: number of runs with the same configuration.
  OUTPUT: avgFitness: average fitness of 'repeat' COMETS runs with the same configuration (due to it is not deterministic)
          sdFitness: standard deviation of fitness during 'repeat' COMETS runs (see above)
  '''

  if not(os.path.exists('ModelsInput/iSynecho_cscBandSPS_over.mat')):
      initialize_models()

  # Determine initial biomasses.
  biomass1=biomassSynecho
  biomass2=biomassKT

  maxBiomass=5 # maximum to normalize increment in biomass in fitBiomass as part of fitness function.
  maxPha=25 # maximum to normalize increment in biomass in fitBiomass as part of fitness function.

  if(maxCycles > -1):
      maxCycles2=int(maxCycles)
  else:
      maxCycles2=1000
  
  print("Fitness function:"+fitFunc)

  # Single GEMs parameter modifications
  # ===================================  
  if not(os.path.exists('strain_1_tmp.mat.cmt')):
    # 1.1.- [COBRApy] Establish modifications in model 1 
    model=cobra.io.load_matlab_model('ModelsInput/iSynecho_cscBandSPS_over.mat')
    # To un-limit the sucrose production, for the flux variability analysis
    model.reactions.get_by_id('SUCRtex').bounds=(-1000,1000)
    dictSucrValue=cobra.flux_analysis.variability.flux_variability_analysis(model,{'EX_sucr(e)'},fraction_of_optimum=1-(sucrPer/100))
    sucrLimit=dictSucrValue['EX_sucr(e)']['maximum']
    model.reactions.get_by_id('SUCRtex').bounds=(sucrLimit,1000)
    model.reactions.get_by_id('EX_sucr(e)').bounds=(sucrLimit,sucrLimit)
    cobra.io.save_matlab_model(model,'strain_1_tmp.mat','model')
    del(model)

    # 1.2.1.- [COBRApy] Establish modifications in model 2.1 (when KT is growing)
    # To put the same uptakes in transporters (*tex) that in Exchange reactions, due to COMETS limits with *tex rxn's rather than EX_ rxn's.
    model=cobra.io.load_matlab_model('ModelsInput/iJN1411_sucr_notNO3_PHA.mat')
    model.reactions.get_by_id('EX_sucr(e)').bounds=(-3.1,0)
    model.reactions.get_by_id('SUCRtex').bounds=(0,3.1)
    cobra.io.save_matlab_model(model,'strain_2_tmp.mat','model')

    # 1.2.2.- [COBRApy] Establish modifications in model 2.2 (when NH4 is exhausted and it produces PHA)
    # To put the same uptakes in transporters (*tex) that in Exchange reactions, due to COMETS limits with *tex rxn's rather than EX_ rxn's.
    model=cobra.io.load_matlab_model('ModelsInput/iJN1411_sucr_notNO3_PHA.mat')
    model.reactions.get_by_id('EX_nh4(e)').bounds=(0,0)
    model.reactions.get_by_id('EX_sucr(e)').bounds=(-3.1,0)
    model.reactions.get_by_id('SUCRtex').bounds=(0,3.1)
    model.reactions.get_by_id('C80aPHAtex').bounds=(0,1000) 
    model.reactions.get_by_id('DM_C80aPHA').bounds=(0,0)
    # PHA production proportional to sucrose intakes
    coeff=float(1.83/3.1) # 0.59032258: 3.1 sucr generates 1.83 PHA in the single model in COBRA
    model.reactions.get_by_id('SUCRtex').subtract_metabolites({model.metabolites.get_by_id('C80aPHA[c]'): coeff})
    model.reactions.get_by_id('SUCRtex').subtract_metabolites({model.metabolites.get_by_id('C80aPHA[e]'): -coeff})
    cobra.io.save_matlab_model(model,'strain_2_b_tmp.mat','model')
    del(model)
    
    # 2.- [python] 
    mat_to_comets('strain_1_tmp.mat')
    mat_to_comets('strain_2_tmp.mat')
    mat_to_comets('strain_2_b_tmp.mat')

    # Community parameter modifications
    # =================================            
    # 4.- [shell script] Write automatically the COMETS parameter about initial biomass of 3 strains, depending on proportions, and initial media concentrations.
    massedit.edit_files(['synKtPHA_layout_template.txt'],["re.sub(r'XXX','"+str(biomass1)+"',line)"], dry_run=False)
    massedit.edit_files(['synKtPHA_layout_template.txt'],["re.sub(r'YYY','"+str(biomass2)+"',line)"], dry_run=False)
    massedit.edit_files(['synKtPHA_layout_template.txt'],["re.sub(r'XXNH4XX','"+str(nh4)+"',line)"], dry_run=False)
  # end-if building models

  # 5.- [COMETS by command line] Run COMETS
  if not(os.path.exists('IndividualRunsResults')):
    os.makedirs('IndividualRunsResults')
  totfitness=0
  sumPha=0
  sumSucr=0
  fitnessList=[]
  # To repeat X times, due to random behaviour in COMETS. In this synKtPHA case, repeat could be 1, because we assume sucrose must be produced by Synecho before KT takes it, so we fix the strain models run per cycle to 1)Synecho 2)KT.
  for i in range(repeat):
        with open("output1.txt", "w") as f:
            subprocess.call(['./comets_scr','comets_script_template'], stdout=f)

        # 6.- [R call] Run script to generate one graph:
        title=str(sucrPer)+'-'+str(biomass1)+'-'+str(biomass2)+'-'+str(nh4)
        print(title)
        subprocess.call(["../../Scripts/plot_biomassX2_vs_3mediaItem.sh 'template1' 'sucr' 'nh4' 'C80aPHA' '"+str(50)+"' '"+str(title)+"' 'blue' 'black' 'darkmagenta' 'Synecho' 'KT'"],shell=True)

        # 7.1.- Determine endCycle: when nh4 is exhausted
        with open("biomass_vs_sucr_nh4_C80aPHA_template1.txt", "r") as sources:        
            lines = sources.readlines()
            iniPointV=lines[0].split()
            iniBiomass=float(iniPointV[1])+float(iniPointV[2])
            endCycle=0
            for line in lines:
                #endCycle=int(line.split()[0])
                nh4Conc=float(line.split()[4])
                if(nh4Conc<float(0.01)):
                    endCycle=int(line.split()[0])
                    break;
            if(endCycle==0):
                endCycle=int(line.split()[0])
                return 0,0; # If after 72h the NH4 is not exhausted, PHA will not be generated!!
            finalBiomassV=lines[endCycle].split()
        biomass1New=float(finalBiomassV[1])
        biomass2New=float(finalBiomassV[2])
        # Get metabolite value in endCycle (at the end of first phase) in a python dictionary
        subprocess.call(["../../Scripts/get_media_composition_oneCycle.sh 'template1' '"+str(endCycle)+"'"],shell=True)
        fileMedia="media_cycle_"+str(endCycle)+".txt"
        metDict = {}
        with open(fileMedia) as f:
            reader = csv.reader(f,delimiter='\t')
            metDict= {rows[0]:rows[1] for rows in reader}
        # Read and write new layout
        if os.path.exists('synKtPHA_layout_template2.txt'): # delete previous content
            os.remove("synKtPHA_layout_template2.txt") 
        with open("synKtPHA_layout_template.txt", "r") as layIn:
            with open("synKtPHA_layout_template2.txt", "a") as layOut:
                lines = layIn.readlines()
                for line in lines:
                    if 'model_file' in line:
                        layOut.write("model_file\tstrain_1_tmp.mat.cmt\tstrain_2_b_tmp.mat.cmt\n")
                    elif '[e]' in line:
                        met=re.sub('\[e\]',r'',line.split()[0])
                        layOut.write("\t\t\t"+met+"[e]\t"+metDict[met]+"\n")
                    elif line.startswith('\t\t0\t0'):
                        layOut.write("\t\t0\t0\t"+str(biomass1New)+"\t"+str(biomass2New)+"\n")
                    elif 'maxCycles' in line:
                        layOut.write("    maxCycles = "+str(maxCycles2)+"\n")
                    elif 'totalbiomasslogname' in line:
                        layOut.write("    totalbiomasslogname = total_biomass_log_template2.txt\n")
                    elif 'medialogname' in line:
                        layOut.write("    medialogname = media_log_template2.txt\n")
                    elif 'fluxlogname' in line:
                        layOut.write("    fluxlogname = flux_log_template2.txt\n")
                    else: # if not line to change, directly copy them
                        layOut.write(line)                    
        # Rename files to avoid to change COMETS files                
        shutil.move('synKtPHA_layout_template.txt','synKtPHA_layout_template1.txt')
        shutil.move('synKtPHA_layout_template2.txt','synKtPHA_layout_template.txt') 
        # 2nd COMETS run
        with open("output2.txt", "w") as f:
            subprocess.call(['./comets_scr','comets_script_template'], stdout=f)
        # [R call] Run script to generate one graph:
        title=str(sucrPer)+'-'+str(biomass1New)+'-'+str(biomass2New)+'-'+str(nh4)
        print(title)
        subprocess.call(["../../Scripts/plot_biomassX2_vs_3mediaItem.sh 'template2' 'sucr' 'nh4' 'C80aPHA' '"+str(maxCycles2/10)+"' '"+str(title)+"' 'blue' 'black' 'darkmagenta' 'Synecho' 'KT'"],shell=True)

        # Generate combined files (biomass, flux, media) with output COMETS 1 and 2:
        # A.-biomass
        #   head 1-n template1.txt + template2.txt (without header or the first line wiht the same values)
        subprocess.call(["head -n"+str(endCycle+1)+" total_biomass_log_template1.txt > total_biomass_log_template.txt"],shell=True)
        subprocess.call(["tail -n"+str(maxCycles2)+" total_biomass_log_template2.txt > temp_biomass2.txt"],shell=True)
        count=endCycle+1
        with open("temp_biomass2.txt", "r") as fin:
            with open("total_biomass_log_template.txt", "a") as fout:
                lines = fin.readlines()
                for line in lines:
                    fout.write(str(count)+"\t"+str(line.split()[1])+"\t"+str(line.split()[2])+"\n")
                    count=count+1
        os.remove("temp_biomass2.txt")
        # B.-media
        #egrep media_n+1{1} --> no.line
        #head 1-no.line template1.txt + template 2.txt, without header and replacing media_i by i=i+n
        # First file fragment
        cmd="grep -n 'media_"+str(endCycle+1)+"{1}' media_log_template1.txt | cut -d: -f1"
        numLine1=int(subprocess.check_output(cmd,shell=True).decode('utf-8').strip())
        subprocess.call(["head -n"+str(numLine1-1)+" media_log_template1.txt > media_log_template.txt"],shell=True)
        # Second file fragment, replacing no.cycles consecutive to the last in first fragment
        cmd="grep -n 'media_1{1}' media_log_template2.txt | cut -d: -f1"
        numLine2=int(subprocess.check_output(cmd,shell=True).decode('utf-8').strip())
        cmd="wc -l media_log_template2.txt | cut -d' ' -f1"
        totLines2=int(subprocess.check_output(cmd,shell=True).decode('utf-8').strip())
        subprocess.call(["tail -n"+str(totLines2-numLine2+1)+" media_log_template2.txt > temp_media2.txt"],shell=True)
        for x in range(1,maxCycles2+1): # +1 because max in range(1,range) is no.iterations+1
            subprocess.call(["egrep '^media_"+str(x)+"\{' temp_media2.txt | sed 's/media_"+str(x)+"{/media_"+str(x+endCycle)+"{/' >> media_log_template.txt"],shell=True)
        os.remove("temp_media2.txt")
        # C.-fluxes
        # fluxes{cycle}{1}{1}{modelNumber}
        # First file fragment
        cmd="grep -n 'fluxes{"+str(endCycle+1)+"}{1}{1}{1}' flux_log_template1.txt | cut -d: -f1"
        numLine1=int(subprocess.check_output(cmd,shell=True).decode('utf-8').strip())
        subprocess.call(["head -n"+str(numLine1-1)+" flux_log_template1.txt > flux_log_template.txt"],shell=True)
        # Second file fragment, replacing no.cycles consecutive to the last in first fragment
        # Not to remove any cycle, because the first one is different, given the last biomass and media composition in first part. Here there isn't cycle=0.
        for x in range(1,maxCycles2+1):
            subprocess.call(["egrep '^fluxes\{"+str(x)+"\}' flux_log_template2.txt | sed 's/fluxes{"+str(x)+"}/fluxes{"+str(x+endCycle)+"}/' >> flux_log_template.txt"],shell=True)                    

        # Plot combined
        title=str(sucrPer)+'-'+str(biomass1)+'-'+str(biomass2)+'-'+str(nh4)
        print(title)
        subprocess.call(["../../Scripts/plot_biomassX2_vs_4mediaItem.sh 'template' 'so4' 'no3' 'pi' 'hco3' '"+str(100)+"' '"+str(title)+"' 'blue' 'cyan' 'black' 'darkmagenta' 'Synecho' 'KT'"],shell=True)
        
        # 7.- Compute fitness (measure to optimize):
        # 7.1.- Determine endCycle: maxCycle
        cmd="wc -l total_biomass_log_template.txt | cut -d' ' -f1"
        maxCycle=-1+int(subprocess.check_output(cmd,shell=True).decode('utf-8').strip())
        with open("biomass_vs_so4_no3_pi_hco3_template.txt", "r") as sources:        
            lines = sources.readlines()
            iniPointV=lines[0].split()
            iniBiomass=float(iniPointV[1])+float(iniPointV[2])
            if(maxCycles>-1):
                endCycle=maxCycles2
            else: # compute end when no3, so4 or pi is exhausted
                endCycle=0
                for line in lines:
                    so4Conc=float(line.split()[3])
                    no3Conc=float(line.split()[4])
                    piConc=float(line.split()[5])
                    #hco3Conc=float(line.split()[6])
                    if(so4Conc<float(0.0001) or no3Conc<float(0.0001) or piConc<float(0.0001)):
                        #    #if(hco3Conc<float(0.0001)):
                        endCycle=int(line.split()[0])
                        break;
                if(endCycle==0):
                    endCycle=maxCycles2
            finalBiomassV=lines[endCycle].split()

        # To measure products
        subprocess.call(["../../Scripts/plot_biomassX2_vs_3mediaItem.sh 'template' 'sucr' 'nh4' 'C80aPHA' '"+str(float(endCycle/10))+"' '"+str(title)+"' 'blue' 'black' 'darkmagenta' 'Synecho' 'KT'"],shell=True)
        with open("biomass_vs_sucr_nh4_C80aPHA_template.txt", "r") as sources:        
            lines = sources.readlines()
        finalLineV=lines[endCycle].split()
        totSucr=float(finalLineV[3])
        totPha=float(finalLineV[5])
        print(str(totPha)+" PHA in cycle "+str(endCycle))
        finalBiomass=float(finalBiomassV[1])+float(finalBiomassV[2])
        
        # 7.2.- Compute fitness: maximize PHA
        fitTime=1-(float(endCycle)/float(maxCycle))
        fitBiomass=float((finalBiomass-iniBiomass)/maxBiomass)
        fitPHA=float(totPha/maxPha)
        
        if(fitFunc=='MaxPHA'):
            fitness=fitPHA
        elif(fitFunc=='PHA_Biomass'):
            fitness=float(0.5*fitPHA+0.5*fitBiomass)

        print(" Fitness: "+str(round(fitness,6))+" in cycle "+str(endCycle))

        totfitness=totfitness+fitness
        fitnessList.append(fitness)
        sumPha=sumPha+totPha
        sumSucr=sumSucr+totSucr

        # Copy individual solution
        file='IndividualRunsResults/'+'biomass_vs_sucr_nh4_C80aPHA_run'+str(i)+'_'+str(fitness)+'_'+str(endCycle)+'.pdf'
        shutil.move('biomass_vs_sucr_nh4_C80aPHA_template_plot.pdf',file)        
        if(dirPlot != ''):
            file2=dirPlot+'biomass_'+str(sucrPer)+'_'+str(biomass1)+'_'+str(biomass2)+'_'+str(nh4)+'_run'+str(i)+'_'+str(fitness)+'_'+str(endCycle)+'.pdf'
            shutil.move(file,file2)
        file='IndividualRunsResults/'+'total_biomass_log_run'+str(i)+'.txt'
        shutil.move('total_biomass_log_template.txt',file)
        file='IndividualRunsResults/'+'media_log_run'+str(i)+'.txt'
        shutil.move('media_log_template.txt',file)
        file='IndividualRunsResults/'+'flux_log_run'+str(i)+'.txt'
        shutil.move('flux_log_template.txt',file)   

  avgfitness=totfitness/repeat
  if(repeat>1):
      sdfitness=statistics.stdev(fitnessList)
  else:
      sdfitness=0.0
  avgPha=sumPha/repeat
  avgSucr=sumSucr/repeat
  print("Fitness_function\tconfiguration\tfitness\tsd\tC80aPHA(mM)\tsucr(mM)\tendCycle")
  print(fitFunc+"\t"+str(sucrPer)+","+str(biomassSynecho)+","+str(biomassKT)+","+str(nh4)+"\t"+str(round(avgfitness,6))+"\t"+str(sdfitness)+"\t"+str(round(avgPha,6))+"\t"+str(round(avgSucr,6))+"\t"+str(endCycle))
  with open(dirPlot+"configurationsResults"+fitFunc+".txt", "a") as myfile:
      myfile.write("Fitness_function\tconfiguration\tfitness\tsd\tC80aPHA(mM)\tsucr(mM)\tendCycle\n")
      myfile.write(fitFunc+"\t"+str(sucrPer)+","+str(biomassSynecho)+","+str(biomassKT)+","+str(nh4)+"\t"+str(round(avgfitness,6))+"\t"+str(sdfitness)+"\t"+str(round(avgPha,6))+"\t"+str(round(avgSucr,6))+"\t"+str(endCycle)+"\n")
  
  print("Avg.fitness(sd):\t"+str(avgfitness)+"\t("+str(sdfitness)+")\n")
  if(sdfitness>0.1):
      avgfitness=0.0
  
  return avgfitness,sdfitness
# end-def ecolLongTermFLYCOP_oneConf
################################################################



