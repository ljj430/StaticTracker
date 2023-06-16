package edu.concordia.junjie;

import org.apache.commons.lang3.tuple.ImmutablePair;
import org.eclipse.jgit.lib.Repository;
import org.refactoringminer.api.*;
import org.refactoringminer.rm1.GitHistoryRefactoringMinerImpl;
import org.refactoringminer.util.GitServiceImpl;

import java.sql.SQLOutput;
import java.util.*;

class RefactoringFormate{
    RefactoringType refactoringType;
    List<gr.uom.java.xmi.diff.CodeRange> refactoringLeft;
    List<gr.uom.java.xmi.diff.CodeRange> refactoringRight;
    String commit;

    Set<ImmutablePair<String,String>> classBefore;
    Set<ImmutablePair<String,String>> classAfter;

    RefactoringFormate(RefactoringType refactoringType, List<gr.uom.java.xmi.diff.CodeRange> refactoringLeft,
                       List<gr.uom.java.xmi.diff.CodeRange> refactoringRight, String commit,
                       Set<org.apache.commons.lang3.tuple.ImmutablePair<String,String>> classBefore, Set<org.apache.commons.lang3.tuple.ImmutablePair<String,String>> classAfter){
        this.refactoringType = refactoringType;
        this.refactoringLeft = refactoringLeft;
        this.refactoringRight = refactoringRight;
        this.commit=commit;
        this.classBefore = classBefore;
        this.classAfter = classAfter;
    }
    public String toString(){
        return this.refactoringType.toString();
    }
    public void setRefactoringType(RefactoringType refactoringType) {
        this.refactoringType = refactoringType;
    }

    public void setRefactoringLeft(List<gr.uom.java.xmi.diff.CodeRange> refactoringLeft) {
        this.refactoringLeft = refactoringLeft;
    }

    public void setRefactoringRight(List<gr.uom.java.xmi.diff.CodeRange> refactoringRight) {
        this.refactoringRight = refactoringRight;
    }

    public void setCommit(String commit) {
        this.commit = commit;
    }

    public void setClassBefore(Set<ImmutablePair<String,String>> classBefore) {
        this.classBefore = classBefore;
    }

    public void setClassAfter(Set<ImmutablePair<String,String>> classAfter) {
        this.classAfter = classAfter;
    }


    public RefactoringType getRefactoringType(){
        return this.refactoringType;
    }

    public List<gr.uom.java.xmi.diff.CodeRange> getRefactoringLeft() {
        return this.refactoringLeft;
    }

    public List<gr.uom.java.xmi.diff.CodeRange> getRefactoringRight() {
        return this.refactoringRight;
    }

    public String getCommit() {
        return this.commit;
    }

    public Set<ImmutablePair<String,String>> getClassBefore() {
        return this.classBefore;
    }

    public Set<ImmutablePair<String,String>> getClassAfter() {
        return this.classAfter;
    }
}
public class RefactoringInfo {
    public static List<RefactoringFormate> getRefactoringInfo(String repoPath,String githubPath, String commit){
        GitService gitService = new GitServiceImpl();
        GitHistoryRefactoringMiner miner = new GitHistoryRefactoringMinerImpl();
        List<RefactoringFormate> refactoringInfo = new ArrayList<>();
        //args[0] = repoPath
        //args[1] = github path
        //args[2] = star commit
        //args[3] = end commit

        // return a
        try {
            Repository repo = gitService.cloneIfNotExists(
                    repoPath, githubPath);


            // start commit: 2a56db09571164d94ddab1ec6f4a8a766e615acc
            // end commit: 09936b57fc90b5a3c7fe530358a2c6a757c32839
//            miner.detectBetweenCommits(repo,startCommit,endCommit,
            miner.detectAtCommit(repo,commit,
                    new RefactoringHandler() {
                        @Override
                        public void handle(String commitId, List<Refactoring> refactorings) {
//                            System.out.println("Refactorings at " + commitId);
                            for (Refactoring ref : refactorings) {
//                                System.out.println("Refactorings at " + commitId);
//                                System.out.println(ref.getInvolvedClassesAfterRefactoring());
                                RefactoringFormate oneRefactoring = new RefactoringFormate(ref.getRefactoringType(),
                                            ref.leftSide(),ref.rightSide(), commitId,
                                            ref.getInvolvedClassesBeforeRefactoring(), ref.getInvolvedClassesAfterRefactoring());
                                refactoringInfo.add(oneRefactoring);
                            }
                        }
                    });

        }
        catch(Exception ex){
            //todosomething
            System.out.println(ex);
            System.out.println("error");
        }

        return refactoringInfo;
    }




//    public static HashMap<String,HashSet<RefactoringFormate>> getRefactoringInfo(String repoPath,String githubPath, String startCommit, String endCommit){
//        GitService gitService = new GitServiceImpl();
//        GitHistoryRefactoringMiner miner = new GitHistoryRefactoringMinerImpl();
//        HashMap<String, HashSet<RefactoringFormate>> refactoringInfo = new HashMap<>();
//        //args[0] = repoPath
//        //args[1] = github path
//        //args[2] = star commit
//        //args[3] = end commit
//
//        // return a
//        try {
//            Repository repo = gitService.cloneIfNotExists(
//                    repoPath, githubPath);
//
//
//            // start commit: 2a56db09571164d94ddab1ec6f4a8a766e615acc
//            // end commit: 09936b57fc90b5a3c7fe530358a2c6a757c32839
////            miner.detectBetweenCommits(repo,startCommit,endCommit,
//            miner.detectBetweenCommits(repo,startCommit,endCommit,
//                    new RefactoringHandler() {
//                        @Override
//                        public void handle(String commitId, List<Refactoring> refactorings) {
//
//                            for (Refactoring ref : refactorings) {
//                                System.out.println("Refactorings at " + commitId);
//                                boolean flag=refactoringInfo.containsKey(commitId);
//                                if(flag){
//                                    HashSet<RefactoringFormate> tmp = refactoringInfo.get(commitId);
//                                    RefactoringFormate oneRefactoring = new RefactoringFormate(ref.getRefactoringType(),
//                                            ref.leftSide(),ref.rightSide(), commitId,
//                                            ref.getInvolvedClassesBeforeRefactoring(), ref.getInvolvedClassesAfterRefactoring());
//                                    tmp.add(oneRefactoring);
//                                    refactoringInfo.put(commitId,tmp);
//                                }
//                                else{
//                                    HashSet<RefactoringFormate> oneCommitRefactoringInfo= new HashSet<>();
//                                    RefactoringFormate oneRefactoring = new RefactoringFormate(ref.getRefactoringType(),
//                                            ref.leftSide(),ref.rightSide(), commitId,
//                                            ref.getInvolvedClassesBeforeRefactoring(), ref.getInvolvedClassesAfterRefactoring());
//                                    oneCommitRefactoringInfo.add(oneRefactoring);
//                                    refactoringInfo.put(commitId,oneCommitRefactoringInfo);
//                                }
//
//
//
//                            }
//                        }
//                    });
//
//        }
//        catch(Exception ex){
//            //todosomething
//        }
//
//        return refactoringInfo;
//    }
    public static void main(String[] args){
        List<RefactoringFormate> forTest = new ArrayList<>();
//        String repoPath = "/Users/lijunjie/Desktop/Master/testProject/jclouds";
        String repoPath = "/home/junjie/Desktop/tracking_static/data_11_6/repos/jclouds";
        String githubPath = "https://github.com/jclouds/jclouds";
//        String githubPath = "https://github.com/google/guava";
//        String commit = "250722e";//1
//        String commit = "b88516f";//2
        String commit = "9dc85ec";//3
        forTest = getRefactoringInfo(repoPath,githubPath,commit);
        for(RefactoringFormate eachRefactoring: forTest){
//            if("MOVE_AND_INLINE_OPERATION" == eachRefactoring.getRefactoringType().toString()) {


                System.out.println(eachRefactoring.getRefactoringType());
                System.out.println("before\n " + eachRefactoring.getClassBefore());
                System.out.println("left\n " + eachRefactoring.getRefactoringLeft());
            System.out.println("after\n " + eachRefactoring.getClassAfter());
            System.out.println("right\n " + eachRefactoring.getRefactoringRight());
//            }

//            if(eachRefactoring.getRefactoringType().toString().equals("RENAME_ATTRIBUTE")
//                    ||eachRefactoring.getRefactoringType().toString().equals("RENAME_PARAMETER")
//                    ||eachRefactoring.getRefactoringType().toString().equals("RENAME_VARIABLE")){
//                System.out.println(eachRefactoring.getRefactoringLeft());
//                System.out.println(eachRefactoring.getRefactoringRight());
//            }
//            System.out.println(eachRefactoring.getRefactoringLeft());
//            System.out.println(eachRefactoring.getRefactoringRight());


        }

//        for(String key : forTest.keySet()){
//            System.out.println("commit size:"+forTest.size());
//            HashSet<RefactoringFormate> value = forTest.get(key);
//            System.out.println("refactoring size:"+value.size());
//            System.out.println(key);
//            for(RefactoringFormate eachRefactoring: value){
//                System.out.println(key+":One refactoring:type:"+eachRefactoring.getRefactoringType());
//                System.out.println(key+":One refactoring:left:"+eachRefactoring.getRefactoringLeft());
//                System.out.println(key+":One refactoring:right:"+eachRefactoring.getRefactoringRight());
//                System.out.println(key+":One refactoring:classbefore:"+eachRefactoring.getClassBefore());
//                System.out.println(key+":One refactoring:classafter:"+eachRefactoring.getClassAfter());
//            }
//
//        }

        //args[0] = repoPath
        //args[1] = github path
        //args[2] = star commit
        //args[3] = end commit

        // return a



//        GitService gitService = new GitServiceImpl();
//        GitHistoryRefactoringMiner miner = new GitHistoryRefactoringMinerImpl();
//
//        try {
//            Repository repo = gitService.cloneIfNotExists(
//                    "/Users/lijunjie/Desktop/Master/testProject/jclouds",
//                    "https://github.com/jclouds/jclouds");
//            HashMap<String,Object> refactoringInfo = new HashMap<>();
//
//            // start commit: 2a56db09571164d94ddab1ec6f4a8a766e615acc
//            // end commit: 09936b57fc90b5a3c7fe530358a2c6a757c32839
//            miner.detectBetweenCommits(repo,"2a56db0","09936b5",
//                    new RefactoringHandler() {
//                        @Override
//                        public void handle(String commitId, List<Refactoring> refactorings) {
//                            System.out.println("Refactorings at " + commitId);
//                            for (Refactoring ref : refactorings) {
//                                refactoringInfo.put("refactoring type",ref.getRefactoringType());
//                                refactoringInfo.put("left side",ref.leftSide());
//                                refactoringInfo.put("right Side", ref.rightSide());
//                                refactoringInfo.put("class before", ref.getInvolvedClassesBeforeRefactoring());
//                                refactoringInfo.put("class after", ref.getInvolvedClassesAfterRefactoring());
//
//
//                                System.out.println("Refactoring type:"+refactoringInfo.get("refactoring type"));
//                                System.out.println("Left Side"+ ref.leftSide());
//                                System.out.println("Right Side"+ ref.rightSide());
//                                System.out.println("Class before refactoring:"+ref.getInvolvedClassesBeforeRefactoring());
//                                System.out.println("Class after refactoring"+ref.getInvolvedClassesAfterRefactoring());
//                            }
//                        }
//                    });
//        }
//        catch(Exception ex){
//            //todosomething
//        }
    }

}
